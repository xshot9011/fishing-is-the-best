import pandas as pd
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt

fig, ax = plt.subplots()

def animation(_):
    data = pd.read_csv('data.csv')
    x = data['x_value']
    y = data['y_value']
    plt.plot(x, y)

    
    # Limit x and y lists to 10 items
    x = x[-300:]
    y = y[-300:]
    # Draw x and y lists
    ax.clear()
    ax.plot(x, y)
    # Format plot
    plt.xticks(rotation=45, ha='right')
    plt.subplots_adjust(bottom=0.20)

ani = FuncAnimation(plt.gcf(), animation, interval=200)
plt.show()