# -*- coding: utf-8 -*-
"""
Created on Wed May 26 15:59:01 2021

@author: CAPUANO-P
"""

import kivy

from array import array
from threading import Thread
from time import time

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics.texture import Texture

class MandelApp(App):
    
    def __init__(self):
        super(MandelApp, self).__init__()
        
        self.rendering = False
        
    def on_render_start(self, *args, **kwargs):
        if not self.rendering:
            print("Start rendering!")
            
            self.image = self.root.ids["image"]
            self.texture = Texture.create(size=self.image.size)
            self.start_time = time()
            
            size = self.image.size[0] * self.image.size[1] * 3
            buf = [255 for x in range(size)]
            self.array = array('B', buf)

            self.scheduler = Clock.schedule_interval(self.on_timer, 1/20.0)
            
            self.rendering = True
            self.renderer = Thread(target=self.render_mandel)
            self.renderer.start()
        else:
            print("Still rendering")
        
        return True
    
    def on_render_stop(self, *args, **kwargs):
        if self.rendering:
            print("Stop rendering!")
            
            self.scheduler.cancel()
            self.rendering = False
            self.renderer.join()
        else:
            print("Not rendering")
        
        return True
    
    def render_mandel(self):
        
        def mandel(c, max_iter=255):
            z = c
            
            for i in range(max_iter):
                z = z*z + c
                
                if abs(z) > 2:
                    return i
            
            return max_iter
        
        for y in range(self.image.height):
            for x in range(self.image.width):
                if not self.rendering:
                    print(f"Aborting rendering at x={x}, y={y}")
                    return
                
                c = -2.0 + 2.5* x / self.image.width + 1j * (-1.25 + 2.5 * y / self.image.height)
                iter = mandel(c)
                
                self.array[3 * (x + y * self.image.width) + 0] = 255 - iter
                self.array[3 * (x + y * self.image.width) + 1] = abs(255 - iter * 4) % 256
                self.array[3 * (x + y * self.image.width) + 2] = abs(255 - iter * 8) % 256
    
        self.rendering = False
        print(f"Rendering complete! time spent: {time() - self.start_time:5.3g}")
    
    def on_timer(self, *args, **kwargs):
        self.texture.blit_buffer(self.array, colorfmt='rgb', bufferfmt='ubyte')
        self.image.texture = self.texture

        self.image.canvas.ask_update()
        
        return self.rendering


if __name__ == '__main__':
    MandelApp().run()