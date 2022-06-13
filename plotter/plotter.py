import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd

# load penguns data with Pandas read_csv
from matplotlib import image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

figure, axis = plt.subplots(2)
plt.subplots_adjust(left=0.1,
                    bottom=0.1,
                    right=0.9,
                    top=0.9,
                    wspace=0.4,
                    hspace=0.4)
axis[0].axis([0, 6, 0, 20])
# make scatter plot
axis[0].set(xlabel="Culmen Length (mm)")
axis[0].set(ylabel="Culmen Depth (mm)")
# add first rectangle with patches
left, bottom, width, height = 0, 0, 3, 4
rect = mpatches.Rectangle((left, bottom), width, height,
                          fill=False,
                          alpha=1,
                          color="purple",
                          linewidth=0.5)
axis[0].add_patch(rect)
axis[0].text(0, 0, '->', horizontalalignment='center', verticalalignment='center')

arr_lena = mpimg.imread('./plotter/arbitrary.png')

imagebox = OffsetImage(arr_lena, zoom=0.3)

ab = AnnotationBbox(imagebox, (3, 10), frameon=False, pad=0)
axis[0].add_artist(ab)

# add second rectangle with patches
left, bottom, width, height = (48, 17.5, 7, 4)
rect = mpatches.Rectangle((left, bottom), width, height,
                          # fill=False,
                          alpha=0.1,
                          # color="purple",
                          # linewidth=2,
                          facecolor="green")
plt.gca().add_patch(rect)

plt.show()