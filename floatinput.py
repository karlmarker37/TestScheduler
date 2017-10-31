from kivy.uix.textinput import TextInput
import re
class FloatInput(TextInput):
    pat1 = re.compile('[^\.0-9]')
    pat2 = re.compile('[^0-9]')
    def insert_text(self, substring, from_undo=False):
        if len(self.text) > 5:
            return super(FloatInput, self).insert_text('', from_undo=from_undo)
        elif self.text.count('.') > 0:
        	s = re.sub(self.pat2,'',substring)
    	else:
    		s = re.sub(self.pat1,'',substring)
    	return super(FloatInput, self).insert_text(s, from_undo=from_undo)