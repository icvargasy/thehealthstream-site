import math

def oklab_to_linear_srgb(L, a, b):
    # From Oklab to LMS
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b

    l = l_**3
    m = m_**3
    s = s_**3

    # From LMS to linear sRGB
    r = +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    b = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s

    return r, g, b

def linear_srgb_to_srgb(c):
    if c <= 0.0031308:
        return 12.92 * c
    else:
        return 1.055 * (c**(1.0 / 2.4)) - 0.055

def oklch_to_hex(L, C, h_deg):
    h = math.radians(h_deg)
    a = C * math.cos(h)
    b = C * math.sin(h)
    
    r_lin, g_lin, b_lin = oklab_to_linear_srgb(L, a, b)
    
    r = linear_srgb_to_srgb(r_lin)
    g = linear_srgb_to_srgb(g_lin)
    b = linear_srgb_to_srgb(b_lin)
    
    # Clamp to [0, 1]
    r = max(0.0, min(1.0, r))
    g = max(0.0, min(1.0, g))
    b = max(0.0, min(1.0, b))
    
    r_val = int(round(r * 255))
    g_val = int(round(g * 255))
    b_val = int(round(b * 255))
    
    return f"#{r_val:02x}{g_val:02x}{b_val:02x}"

def srgb_to_linear_srgb(c):
    if c <= 0.04045:
        return c / 12.92
    else:
        return ((c + 0.055) / 1.055)**2.4

def hex_to_oklch(hex_str):
    hex_str = hex_str.lstrip('#')
    r = int(hex_str[0:2], 16) / 255.0
    g = int(hex_str[2:4], 16) / 255.0
    b = int(hex_str[4:6], 16) / 255.0
    
    r_lin = srgb_to_linear_srgb(r)
    g_lin = srgb_to_linear_srgb(g)
    b_lin = srgb_to_linear_srgb(b)
    
    # From linear sRGB to LMS
    l = 0.4122214708 * r_lin + 0.5363325363 * g_lin + 0.0514459929 * b_lin
    m = 0.2119034982 * r_lin + 0.6806995451 * g_lin + 0.1073969566 * b_lin
    s = 0.0883024619 * r_lin + 0.2817188376 * g_lin + 0.6299787005 * b_lin
    
    l_ = l**(1.0 / 3.0)
    m_ = m**(1.0 / 3.0)
    s_ = s**(1.0 / 3.0)
    
    # From LMS to Oklab
    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    a = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    b = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    
    C = math.sqrt(a**2 + b**2)
    h = math.degrees(math.atan2(b, a))
    if h < 0:
        h += 360.0
        
    return L, C, h

# Test
print("Hex #d9525c to OKLCH:", hex_to_oklch("#d9525c"))
print("oklch(0.68, 0.16, 15) to Hex:", oklch_to_hex(0.68, 0.16, 15))
print("oklch(0.58, 0.16, 15) to Hex:", oklch_to_hex(0.58, 0.16, 15))
