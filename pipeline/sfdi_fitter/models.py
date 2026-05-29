import torch
import torch.nn as nn
import numpy as np

#TODO: давайте обособим это в отдельный подмодуль

class ConvTanh(nn.Module):
    def __init__(self, in_ch, out_ch, line_mode=False, norm="bn"):
        super().__init__()
        k = (7, 1) if line_mode else (7, 7)
        p = (3, 0) if line_mode else (3, 3)

        layers = []
        use_norm = norm is not None and norm.lower() != "none"
        layers.append(nn.Conv2d(in_ch, out_ch, kernel_size=k, padding=p, bias=not use_norm))

        if use_norm:
            n = norm.lower()
            if n == "bn":
                layers.append(nn.BatchNorm2d(out_ch))
            elif n == "gn":
                g = 8 if out_ch % 8 == 0 else 4 if out_ch % 4 == 0 else 1
                layers.append(nn.GroupNorm(g, out_ch))
            elif n == "in":
                layers.append(nn.InstanceNorm2d(out_ch, affine=True))
            else:
                raise ValueError(f"Unknown norm: {norm}")

        layers.append(nn.Tanh())
        self.block = nn.Sequential(*layers)

    def forward(self, x):
        return self.block(x)


class UNetGioux(nn.Module):
    def __init__(self, in_ch=1, out_ch=2, base_ch=8, line_mode=False, norm="bn"):
        super().__init__()
        c1, c2, c3, c4 = base_ch, base_ch*2, base_ch*4, base_ch*8
        cb = c4 * 2

        self.pool = nn.MaxPool2d(2, 2)
        self.up = nn.Upsample(scale_factor=2, mode="nearest")

        self.enc1 = ConvTanh(in_ch, c1, line_mode=line_mode, norm=norm)
        self.enc2 = ConvTanh(c1, c2, line_mode=line_mode, norm=norm)
        self.enc3 = ConvTanh(c2, c3, line_mode=line_mode, norm=norm)
        self.enc4 = ConvTanh(c3, c4, line_mode=line_mode, norm=norm)

        self.bottleneck = ConvTanh(c4, cb, line_mode=line_mode, norm=norm)

        self.dec_deconv4 = nn.ConvTranspose2d(cb, c4, 3, stride=1, padding=1)
        self.dec_conv4 = ConvTanh(c4+c4, c4, line_mode=line_mode, norm=norm)
        self.dec_deconv3 = nn.ConvTranspose2d(c4, c3, 3, stride=1, padding=1)
        self.dec_conv3 = ConvTanh(c3+c3, c3, line_mode=line_mode, norm=norm)
        self.dec_deconv2 = nn.ConvTranspose2d(c3, c2, 3, stride=1, padding=1)
        self.dec_conv2 = ConvTanh(c2+c2, c2, line_mode=line_mode, norm=norm)
        self.dec_deconv1 = nn.ConvTranspose2d(c2, c1, 3, stride=1, padding=1)
        self.dec_conv1 = ConvTanh(c1+c1, c1, line_mode=line_mode, norm=norm)

        k = (7, 1) if line_mode else (7, 7)
        p = (3, 0) if line_mode else (3, 3)
        self.head = nn.Conv2d(c1, out_ch, kernel_size=k, padding=p)

    def forward(self, x):
        s1 = self.enc1(x);       x = self.pool(s1)
        s2 = self.enc2(x);       x = self.pool(s2)
        s3 = self.enc3(x);       x = self.pool(s3)
        s4 = self.enc4(x);       x = self.pool(s4)

        x = self.bottleneck(x)

        x = self.up(x); x = self.dec_deconv4(x); x = torch.cat([x, s4], 1); x = self.dec_conv4(x)
        x = self.up(x); x = self.dec_deconv3(x); x = torch.cat([x, s3], 1); x = self.dec_conv3(x)
        x = self.up(x); x = self.dec_deconv2(x); x = torch.cat([x, s2], 1); x = self.dec_conv2(x)
        x = self.up(x); x = self.dec_deconv1(x); x = torch.cat([x, s1], 1); x = self.dec_conv1(x)

        return self.head(x)