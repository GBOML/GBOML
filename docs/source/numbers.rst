Numbers
=======

GBOML recognizes floating-point numbers and integers. Depending on the context, an integer may be called for, but in contexts where a floating-point number is required, an integer will also be accepted and converted to a floating-point number automatically. It should be noted that scientific notation is supported and automatically converted to floating-point numbers. Accordingly, the following are considered floating-point numbers,

.. math::
    \texttt{1e-5}, \qquad \texttt{-2.5e-10}, \qquad \texttt{2e10}.
