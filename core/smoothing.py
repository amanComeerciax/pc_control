import math
import time

def smoothing_factor(t_e, cutoff):
    r = 2 * math.pi * cutoff * t_e
    return r / (r + 1)

def exponential_smoothing(a, x, x_prev):
    return a * x + (1 - a) * x_prev

class OneEuroFilter:
    """One Euro Filter for smoothing noisy signals."""
    def __init__(self, t0, x0, dx0=0.0, min_cutoff=1.0, beta=0.0, d_cutoff=1.0):
        self.min_cutoff = float(min_cutoff)
        self.beta = float(beta)
        self.d_cutoff = float(d_cutoff)
        self.x_prev = float(x0)
        self.dx_prev = float(dx0)
        self.t_prev = float(t0)

    def __call__(self, t, x):
        t_e = t - self.t_prev
        if t_e <= 0:
            return self.x_prev
            
        # The filtered derivative of the signal
        a_d = smoothing_factor(t_e, self.d_cutoff)
        dx = (x - self.x_prev) / t_e
        dx_hat = exponential_smoothing(a_d, dx, self.dx_prev)
        
        # The filtered signal
        cutoff = self.min_cutoff + self.beta * abs(dx_hat)
        a = smoothing_factor(t_e, cutoff)
        x_hat = exponential_smoothing(a, x, self.x_prev)
        
        self.x_prev = x_hat
        self.dx_prev = dx_hat
        self.t_prev = t
        
        return x_hat

class PointSmoother:
    """Applies One Euro Filter to 2D coordinates."""
    def __init__(self, min_cutoff=0.5, beta=0.1):
        self.filter_x = None
        self.filter_y = None
        self.min_cutoff = min_cutoff
        self.beta = beta

    def __call__(self, x, y):
        t = time.time()
        if self.filter_x is None:
            self.filter_x = OneEuroFilter(t, x, min_cutoff=self.min_cutoff, beta=self.beta)
            self.filter_y = OneEuroFilter(t, y, min_cutoff=self.min_cutoff, beta=self.beta)
            return x, y
        return self.filter_x(t, x), self.filter_y(t, y)
