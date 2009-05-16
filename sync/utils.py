def get_hex_color():
  import random
  return '#'+''.join([hex(random.randint(0,15))[2] for i in range(6)])
