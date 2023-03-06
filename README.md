# Influence Solver

Implementation of an algorithm, that efficiently checks whether a hypothesis is derivable from an influence model, using the proof rules of the "Calculus of Influece". More Information about the model and the algorithm can be extracted from [here](Thesis.pdf).  

Matplotlib is needed to visualize the statements. It can be installed via:
```
pip install matplotlib
```

---  

## Usage  
The **Solver**-class can be used to instantiate a Solver-Object. This solver supports the set-like operators *add, delete* and *discard* to build a model of statements. The statements are 5-tuple, containing the influencing variable, a tuple of two floats indicating the range of the statement, the quality, a tuple of two float indicating the domain of the statement and the influenced variable.  
`tuple[str, tuple[float, float], str, tuple[float, float], str]` 

After building the model, the **solve** method of the solver object can be used to check if a given hypothesis is derivable by the model. The hypothesis can be added using the parameter of the method. It follows the pattern of the statements introduced above.

## Examples
A running example is given in [main.py](main.py). Further examples are in the `examples/` folder.

## Build models
To build own models, the [csv_to_model.py](benchmark/csv_to_model.py) can be used. For that, a csv file is needed.The file should contain two coloums with the name of the variables in the first row. 
The rows below are intepreted as the data points and both columns should have equal 
length. Multiple influences can be joined by added further pairs of columns. 
Examples are in the `data/` folder.

To extract a model from the data points, they are ordered on one axis 
and linear functions are build between adjacent points. Now, an adjustable amount 
of statements of equal width will be inserted and added side by side to the model, centered on the linear functions. The amount of statements, height of the statements and overlapping can be adjusted. Further information can be seen in the corresponding docstring.

