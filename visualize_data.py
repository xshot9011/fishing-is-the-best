import pandas as pd
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt

fig, ax = plt.subplots()

def animation(_):
    data = pd.read_csv('data.csv')
    x = data['x_value']
    y = data['y_value']
    plt.plot(x, y)
    
    x = x[-300:]
    y = y[-300:]
    ax.clear()
    ax.plot(x, y)
    plt.xticks(rotation=45, ha='right')
    plt.subplots_adjust(bottom=0.20)

ani = FuncAnimation(plt.gcf(), animation, interval=200)
plt.show()