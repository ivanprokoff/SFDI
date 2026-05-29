import lmfit.models as lmmodels
import numpy as np
import tqdm
import time
import pandas as pd
import pickle as pkl
from pathlib import Path
from sklearn.impute import SimpleImputer
from sklearn.neighbors import KNeighborsRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import sklearn
from sklearn.metrics import make_scorer
from abc import ABC, abstractmethod

try:
    import eigen_sfdi_fit as cpp_fit
except ImportError:
    cpp_fit = None


def _asset_path(filename):
    package_asset_path = Path(__file__).resolve().parent / 'assets' / filename
    parent_asset_path = Path(__file__).resolve().parents[1] / 'assets' / filename

    for path in (package_asset_path, parent_asset_path):
        if path.exists():
            return str(path)

    return str(package_asset_path)


_MCML_DATAFRAME_PATH = _asset_path('2023-02-27-modeling_results_SFDI.pkl')
_MUS_MCML_REGRESSOR_PATH = _asset_path('knn_mus_pipe.pkl')
_MUA_MCML_REGRESSOR_PATH = _asset_path('knn_mua_pipe.pkl')

_MUS_NN_MCML_REGRESSOR_PATH = _asset_path('backward_mus_reg.pkl')
_MUA_NN_MCML_REGRESSOR_PATH = _asset_path('backward_mua_reg.pkl')
_FORWARD_NN_MCML_MODEL = _asset_path('forward_model.pkl')

MCML_DATAFRAME = pd.read_pickle(_MCML_DATAFRAME_PATH)
_n_freqs_mcml = len(MCML_DATAFRAME['R_k'].iloc[0])

    
class knn_model_selection():


    def __init__(self, df, freqs_ids, coef = 'mus'):
      
        self.X_train = np.array([list(i) for i in df.R_k.values])[:,freqs_ids].astype(np.float32)
        self.y_train = df[coef]
        
        mse_scoring = make_scorer(sklearn.metrics.mean_squared_error,greater_is_better=False)
        KNN = KNeighborsRegressor()

        cv_scheme = sklearn.model_selection.KFold(n_splits=5)

        param_grid = {'KNN__n_neighbors' : [1, 2, 3, 4, 5, 6] ,   'KNN__weights':['distance']}

        KNN_pipe = Pipeline(steps = [('scaler', StandardScaler()),    
                                                      ('KNN',KNN)])
        gridsearcher_default_params = {}
        gridsearcher_default_params['verbose'] = 0
        gridsearcher_default_params['scoring'] = mse_scoring
        gridsearcher_default_params['cv'] = cv_scheme
        self.gs = sklearn.model_selection.GridSearchCV(KNN_pipe, param_grid=param_grid,
                                                           **gridsearcher_default_params)
        self.model_fit()
        
    def model_fit(self):
        self.gs.fit(self.X_train, self.y_train)


class ReflectanceModel(ABC):
    @abstractmethod
    def fit(self, k, R, fit_mask, **kwargs):
        pass

    @abstractmethod
    def evaluate(self, spatial_frequencies, mua=1, mus_prime=10):
        pass

class NNMCMLmodel(ReflectanceModel):
    _avail_strategies = ['max_freq']

    def __init__(self,multiple_frequencies_strategy='max_freq'):
        super().__init__()

        self.forward_model = self._load_model(_FORWARD_NN_MCML_MODEL)
        self.backward_mua  = self._load_model(_MUA_NN_MCML_REGRESSOR_PATH)
        self.backward_mus  = self._load_model(_MUS_NN_MCML_REGRESSOR_PATH)

        self._convert_precision_to_float32()
        self.strategy = multiple_frequencies_strategy
        self._check_strategy()
        
    def _convert_precision_to_float32(self):
        for model in [self.forward_model,self.backward_mua,self.backward_mus]:
            model[-1].coefs_ = [coef.astype(np.float32, copy=False) for coef in model[-1].coefs_]
            model[-1].intercepts_ = [intercept.astype(np.float32, copy=False) for intercept in model[-1].intercepts_]
        
        for model in [self.backward_mua,self.backward_mus]:
            model[0].mean_ = model[0].mean_.astype(np.float32)
            model[0].scale_ = model[0].scale_.astype(np.float32)
    
    def _check_strategy(self):
        ERR_MSG = f"{self.strategy} is not implemented. Use {self._avail_strategies}"
        assert self.strategy in self._avail_strategies,ERR_MSG

    @staticmethod
    def _load_model(path):
        with open(path,'rb') as f:
            model = pkl.load(f)
        return model
    
    def fit(self,k:np.ndarray,R:np.ndarray,
                 fit_mask:np.ndarray,**kwargs):

        f,h,w =  R.shape
        fit_result = {}
        k = np.array(k)
        assert f > 1, 'Multiple frequencies required for fit'

        if fit_mask is None:
            _fit_mask = np.ones((h,w),dtype=np.bool_)
        else:
            assert fit_mask.shape == (h,w),'fit mask should be of shape (h,w)'
            _fit_mask = fit_mask.copy()

        if self.strategy == 'max_freq':
            max_freq_id = np.argmax(k)
            zero_freq_id = np.arange(len(k))[np.where(k < 1e-5)][0]
            _k = k[max_freq_id]

            r0 = R[zero_freq_id][_fit_mask].reshape(-1,1)
            rk = R[max_freq_id][_fit_mask].reshape(-1,1)
            kvec = _k*np.ones_like(r0)

            X = np.hstack([r0,rk,kvec]).astype(np.float32)

            pred_log_mua = self.backward_mua.predict(X).ravel()
            pred_mua = np.power(10,np.clip(pred_log_mua,-3,1))

            pred_log_mus = self.backward_mus.predict(X).ravel()
            pred_mus = np.power(10,np.clip(pred_log_mus,0,5))

            mua_map = -np.ones((h,w),dtype=np.float32)
            mus_map = -np.ones((h,w),dtype=np.float32)
            mua_map[_fit_mask] = pred_mua
            mus_map[_fit_mask] = pred_mus

            fit_result['mua'] = mua_map
            fit_result['mus'] = mus_map

            return fit_result
        else:
            raise NotImplementedError("{self.strategy} is not supported")

    def evaluate(self, spatial_frequencies:np.ndarray, mua:float=1.,
                       mus_prime:float=10.):
        
        _freqs = np.array(spatial_frequencies)
        init_shape = _freqs.shape

        ks = _freqs.reshape(-1,1)
        muavec = mua*np.ones_like(ks)
        musvec = mus_prime*np.ones_like(ks)
        X = np.hstack([muavec,musvec,ks])
        rs = self.forward_model.predict(X).ravel().reshape(init_shape)
        return rs


class MCML_model(ReflectanceModel):
    """
    Implements model for inverse problem solving base on numerical simulation
    """

    def __init__(self, frequency_prepends=None,
                 spatial_frequencies=None,
                 df=MCML_DATAFRAME,freq_prepends_calibration_slope=2*np.pi/160.):
    

        self.df = df
        
        assert (frequency_prepends is not None) or (spatial_frequencies is not None),'Either frequency_prepends or spatial_frequencies should be specified!'
        
        self.freq_prepends_calibration_slope = freq_prepends_calibration_slope
        
        if not frequency_prepends is None:
            self.freqs_ids = [int(i)-1 for i in frequency_prepends]
        
        else:
            self.freqs_ids = self._convert_spatial_frequencies_to_ids(spatial_frequencies)
            
        self.mua_regressor = knn_model_selection(df, self.freqs_ids, 'mua').gs.best_estimator_
        self.mus_regressor = knn_model_selection(df, self.freqs_ids, 'mus').gs.best_estimator_

        self.fix_precision_in_models()
        self.imputer = SimpleImputer(missing_values=np.nan, strategy='constant', fill_value=0)
            
    def fix_precision_in_models(self):
        for model in [self.mua_regressor,self.mus_regressor]:
            model[0].mean_ = model[0].mean_.astype(np.float32)
            model[0].scale_ = model[0].scale_.astype(np.float32)
      
    def fit(self, k, R, fit_mask, **kwargs):
        """
        Fit dependency of diffuse reflectance R on spatial frequencies k
        using diffuse model

        :param k (1d np.array): spatial frequencies of signal
        :param R (1d np.array):
        :param params (lmfit.model.Parameters): parameters of Diffuse model self.model.
        Can be properly generated using self.init_params()

        :param kwargs: additional fitting keyword arguments used for fit (see self.model.fit(**kwargs))
        :return: lmfit.model.ModelResult (fit result of diffuse model)
        """
        
            
        fit_result = {}
        f,h,w =  R.shape
        fit = np.stack(R,-1).reshape(h*w,f)
        fit = self.imputer.fit_transform(fit)
        fit_result['mua'] = self.mua_regressor.predict(fit.astype(np.float32)).reshape(h,w)
        fit_result['mus'] = self.mus_regressor.predict(fit.astype(np.float32)).reshape(h,w)
        
        return fit_result
        
 
   

    def evaluate(self, spatial_frequencies, mua=1, mus_prime=10):
        """
        evaluates diffuse reflectance for given spatial_frequencies,
        absorption coefficient (mua) and reduced scattering coefficient (mus_prime)

        :param spatial_frequencies (float or np.array of floats): spatial frequencies (2pi/L) in mm^-1
        :param mua (float): absorption coefficient of tissue in mm^-1
        :param mus_prime (float): reduced scattering coefficient of tissue in mm^-1
        :return: (float or np.array of floats) diffuse reflectance for given spatial frequencies, mua and mus_prime
        """
        ids = self._convert_spatial_frequencies_to_ids(spatial_frequencies)
                
        arg = self.df.apply(lambda x:(abs( x['mua'] - mua)) / mua
                   + (abs(x['mus'] - mus_prime)) / mus_prime, axis=1).argmin()
        #print(arg)
        return self.df.iloc[arg].R_k[ids]
    
    def _convert_spatial_frequencies_to_ids(self,spatial_frequencies):
        return np.clip(np.array([round(sf/self.freq_prepends_calibration_slope)
                                 for sf in spatial_frequencies]).astype(int)-1,0,_n_freqs_mcml-1)
        
    
class DiffuseModel(ReflectanceModel):
    """
    Implements model for reflectance in diffuse approximation
    R(k) = Aa'/[(mu_eff/mu_tr + 1)(mu_eff/mu_tr + 3A)]

    where a' = mu_s_prime/(mu_s_prime + mu_a)

    available field
    available methods:

    init_params(self)
    fit(self, k,R)
    """

    def __init__(self, n=1.37):
        """
        n (float) - refractive index
        """

        self.n = n
        self.Reff = self._get_Reff()  # Fresnel effective reflection from the surface
        self.A_c = self._get_A_c()
        self.model = lmmodels.ExpressionModel(
            'C*(ms/(ma+ms))/ ((sqrt(x**2+3*ma*(ma+ms))/(ma+ms)+1)*(sqrt(x**2+3*ma*(ma+ms))/(ma+ms)+C)) ')
        
        
        def fit_function(x,ma,ms,C):
            
            mu_tr = ma + ms
            a_prime = ms/mu_tr
            mu_eff = np.sqrt(3*ma*(ma+ms))
            
            numerator = C*a_prime
            mu_eff_prime = (x**2 + mu_eff**2)**(0.5)
            
            denominator = (mu_eff_prime/mu_tr + 1)*(mu_eff_prime/mu_tr + C)
            
            return numerator/denominator
        
        self.fit_func = fit_function
        
        self.new_model = lmmodels.Model(self.fit_func)
            
        
    def _get_Reff(self):
        Reff = 0.0636 * self.n + 0.668 + (0.71 / self.n) - (1.44 / (self.n ** 2))
        return Reff

    def _get_A_c(self):
        return (1 - self.Reff) / (2 * (1 + self.Reff))

    def init_params(self):
        """initialize standard parameters for model
        assuming spatial frequencies are in mm^-1
        and
        """

        params = self.model.make_params()

        params['ma'].value = 0.2
        params['ma'].vary = True
        #params['ma'].max = 10000
        params['ma'].min = 0
        params['C'].value = 3 * self.A_c
        params['C'].vary = False
        #params['ms'].max = 10000
        params['ms'].vary = True
        params['ms'].value = 3
        params['ms'].min = 0.0

        return params

    def fit(self, k, R, params=None, **kwargs):
        """
        Fit dependency of diffuse reflectance R on spatial frequencies k
        using diffuse model

        :param k (1d np.array): spatial frequencies of signal
        :param R (1d np.array):
        :param params (lmfit.model.Parameters): parameters of Diffuse model self.model.
        Can be properly generated using self.init_params()

        :param kwargs: additional fitting keyword arguments used for fit (see self.model.fit(**kwargs))
        :return: lmfit.model.ModelResult (fit result of diffuse model)
        """
        if params is None:
            params = self.init_params()

        return self.model.fit(data=R, params=params, x=k, **kwargs)

    def evaluate(self, spatial_frequencies, mua=1, mus_prime=10,use_old_model=True):
        """
        evaluates diffuse reflectance for given spatial_frequencies,
        absorption coefficient (mua) and reduced scattering coefficient (mus_prime)

        :param spatial_frequencies (float or np.array of floats): spatial frequencies (2pi/L) in mm^-1
        :param mua (float): absorption coefficient of tissue in mm^-1
        :param mus_prime (float): reduced scattering coefficient of tissue in mm^-1
        :return: (float or np.array of floats) diffuse reflectance for given spatial frequencies, mua and mus_prime
        """

        params = self.init_params()
        params['ma'].value = mua
        params['ms'].value = mus_prime

        if use_old_model:
            return self.model.eval(x=spatial_frequencies, params=params)
        return self.new_model.eval(x=spatial_frequencies,params=params)

def calculate_diffuse_reflectance(spatial_frequencies, mua=1., mus_prime=10., refractive_index=1.37, mode='Diffuse', model=DiffuseModel(n=1.37)):
    """
    Calculate diffuse reflectance R(k) for given spatial frequencies
    in diffuse model approximation for given absorption coefficients mua,
    reduced scattering coefficient mus_prime and refractive_index

    Note that all parameters should be of the same physical dimension, i.e. mm^-1, or cm^-1

    :param spatial_frequencies: (list or 1d np.array) of spatial frequencies
    :param mua: (float) absorption coefficient, e.g. 1 mm^-1
    :param mus_prime: (float) reduced scattering, e.g. 10 mm^-1
    :param refractive_index: (float) refractive index of tissue (dimensionless)

    :return: (1d np.array) values of diffuse reflectance for given spatial_frequencies
    """
  
    return model.evaluate(spatial_frequencies, mua=mua, mus_prime=mus_prime)   
        

def get_reflectance_stack(freqs_test, mac_test, freqs_reference, mac_reference, ref_mua=1.,
                          ref_mus_prime=10., refractive_index=1.37, mode='Diffuse', model=DiffuseModel(n=1.37)):
    """
    Calculate reflectance stack based on alternating component of transport function (Mac)
    of test sample and reference sample

    R(k,x,y) = R_ref(k)*Mac_test(k,x,y)/Mac_reference(k,x,y)

    :param freqs_test: (1d np.array) spatial frequencies for test object
    :param mac_test: (3d np.array of shape (len(freqs_test),Nx,Ny)) of  Mac values for different pixels of an image of test object
    :param freqs_reference: (1d np.array) spatial frequencies for reference object
    :param mac_reference: (3d np.array of shape (len(freqs_test),Nx,Ny)) of  Mac values for different pixels of an image of test object
    :param ref_mua: absorption coefficient of reference object
    :param ref_mus_prime: reduced scattering coefficient of reference object
    :param refractive_index: refractive index of reference object
    :return: reflectance 3d np.array stack of shape (len(freqs_test),Nx,Ny) of diffuse reflectance values
    """

    mac_reference_for_freqs = {f: mac for f, mac in zip(freqs_reference, mac_reference)}
    
    reference_diffuse_reflectance = calculate_diffuse_reflectance(freqs_test, mua=ref_mua,
                                                                  mus_prime=ref_mus_prime,
                                                                  refractive_index=refractive_index, mode=mode, model=model)

    mac_reference_reshape = np.stack([mac_reference_for_freqs[f] for f in freqs_test])
    
    return mac_test * reference_diffuse_reflectance.reshape(-1, 1, 1) / mac_reference_reshape


#TODO: implement multithreading with SharedMemory with python
def fit_diffuse_reflectance_stack(frequencies, reflectance_stack, fit_mask, model, 
                                  mode='Diffuse', backend='python', use_tqdm=True):
    """
    Fit diffuse reflectance stack using diffuse or numerical model
    R(k,x,y) ~ DiffuseModel(k,mua,mus_prime), i.e. estimate mua,mus_prime for each pixel
    of an reflectance stack image

    :param frequencies: 1d np.array of spatial frequencies
    :param reflectance_stack: (3d np.array) stack of (len(frequencies), Nx,Ny) shape
    :param fit_mask: (2d np.array of dtype=np.bool of shape (Nx,Ny)) which specifies which pixels should be fitted
    :param diffuse_model: fitter.DiffuseModel() instance with specified refractive index
    :param backend: (str) 'python' or 'cpp'

    :return: fit_results (dict of 'mua','mus','chi2') values for every pixel of an image
    """
    
    assert mode in ['LUT','Diffuse'],'"mode" should be either "LUT" or "Diffuse"'
    
    if mode == 'LUT':
        #print("Using look-up table for fitting model")
        fit_results = model.fit(frequencies, reflectance_stack, fit_mask)
        
        return fit_results
        
    if backend == 'python':  # single processor
        fit_results = {k: np.zeros(reflectance_stack.shape[1:]) for k in ['mua', 'mus', 'chi2','time']}

        x_iterator = tqdm.tqdm(range(reflectance_stack.shape[1])) if use_tqdm else range(reflectance_stack.shape[1])

        for x in x_iterator:
            for y in range(reflectance_stack.shape[2]):
                if fit_mask[x, y]:
                    start_time = time.time()
                    fit_res = model.fit(k=frequencies, R=reflectance_stack[:, x, y])
                    fit_results['mua'][x, y] = fit_res.best_values['ma']
                    fit_results['mus'][x, y] = fit_res.best_values['ms']
                    fit_results['chi2'][x, y] = fit_res.chisqr
                    fit_results['time'][x,y] = time.time() - start_time

        return fit_results

    elif backend == 'cpp':
        if cpp_fit is None:
            raise ImportError("cpp backend requires optional eigen_sfdi_fit module")

        #assure freqs are ascending
        argsort_freqs = np.argsort(frequencies)

        binned = np.swapaxes(np.swapaxes(reflectance_stack[argsort_freqs],0,1),1,2)
        guesses = np.zeros((binned.shape[0], binned.shape[1], 4))

        mu_a = 0.2
        mu_s = 2.
        guesses[:, :, 0] = mu_a  # bounded_to_internal(a1)
        guesses[:, :, 1] = mu_s  # bounded_to_internal(tau1)
        guesses[:, :, 2] = 0.  # bounded_to_internal(a2)
        guesses[:, :, 3] = 0.  # bounded_to_internal(tau2)

        fit_required = fit_mask.astype(int)
        ind_mins = np.zeros(binned.shape[:2], dtype=np.int64)
        ind_maxs = frequencies.shape[0] - 1  # np.abs(ts - ts_upper).argmax()
        ind_maxs *= np.ones_like(ind_mins)

        res = cpp_fit.fit_pixels(frequencies[argsort_freqs], np.ascontiguousarray(binned), np.ascontiguousarray(guesses),
                                 np.ascontiguousarray(fit_required), np.ascontiguousarray(ind_mins), np.ascontiguousarray(ind_maxs))

        res = res.reshape((list(binned.shape[:2])+[5]))
        fit_results = {k:res[:,:,i] for i,k in enumerate(['mua','mus'])}
        fit_results.update({k:np.zeros(binned.shape[:2]) for k in ['chi2','times']})

        return fit_results
    else:
        raise ValueError("Only 'python' (lmfit) and 'cpp' backends are available!")
