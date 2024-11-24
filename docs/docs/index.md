# Welcome to MkDocs

For full documentation visit [mkdocs.org](https://www.mkdocs.org).

## Commands

* `mkdocs new [dir-name]` - Create a new project.
* `mkdocs serve` - Start the live-reloading docs server.
* `mkdocs build` - Build the documentation site.
* `mkdocs -h` - Print help message and exit.

## Project layout

    mkdocs.yml    # The configuration file.
    docs/
        index.md  # The documentation homepage.
        ...       # Other markdown pages, images and other files.


## 定式化


```math
$$
f(x) = \int_{-\infty}^\infty
    \hat f(\xi)\,e^{2 \pi i \xi x}
    \,d\xi
$$
```

$$
f(x) = \int_{-\infty}^\infty
    \hat f(\xi)\,e^{2 \pi i \xi x}
    \,d\xi
$$

インラインで数式を書きます。$`E=mc^2`$
インラインで数式を書きます。$E=mc^2$


$$
\begin{aligned}
&\text{minimize}  & &z_{\text{doc}} + \sum_{k\in K}z_{\text{spe},k} + \sum_{p\in P}z_{\text{skill},p}   \\
&\text{subject to} & &\sum_{i\in I} x_{i,0} = 3,   \\
& & &\sum_{i\in I} x_{i,j} = 4,  & j \in J\setminus \{0\}, \\
& & &\sum_{j\in J} x_{i,j} = 1,  & i \in I, \\
& & &\sum_{i\in I} D_i x_{i,j} \le \left \lfloor \frac{\sum_{i\in I}D_i}{6} +1 \right \rfloor + z_{\text{doc}},  & j \in J\setminus \{0\}, \\
& & &\sum_{i\in I} S_{i,k} x_{i,j} \le \left \lfloor \frac{\sum_{i\in I}S_{i,k}}{6} +1 \right \rfloor + z_{\text{spec},k},  & j \in J\setminus \{0\},\ k\in K, \\
& & &\sum_{i\in I} C_{i,p} x_{i,j} \le \left \lfloor \frac{\sum_{i\in I}C_{i,p}}{6} +1 \right \rfloor + z_{\text{spec},p},  & j \in J\setminus \{0\},\ p\in P. \\
\end{aligned}
$$
