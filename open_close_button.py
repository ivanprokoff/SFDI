import customtkinter


class Button(customtkinter.CTkButton):
    def __init__(self, *args,
                 **kwargs):
        super().__init__(*args, **kwargs)

        self.open_text = None
        self.state = 'Open'
        self.close_text = None
        self.open_commands = None
        self.close_commands = None

    def set_commands(self, open_text, close_text, open_commands, close_commands):
        self.open_text = open_text
        self.close_text = close_text
        self.open_commands = open_commands
        self.close_commands = close_commands
        self.configure(self,  command=open_commands, text=open_text)

    def change_function(self):

        if self.state == 'Closed':
            self.configure(self, command=self.open_commands, text=self.open_text)
            self.state = 'Open'
            self.configure(fg_color="transparent", border_width=1)
            #self.configure(fg_color=['#3a7ebf', '#1f538d'], border_width=0)
        else:
            self.configure(self, command=self.close_commands, text=self.close_text)
            self.state = 'Closed'

            self.configure(fg_color="transparent", border_width=1)
