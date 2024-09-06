Useful Idioms
-------------

Several modeling needs may be readily addressed by using particular idioms that may not be immediately apparent from the GBOML syntax rules.
Such modeling needs are discussed and appropriate idioms to address them are discussed next.

Repeating Data
==============

In some cases, the modeling task calls for repeating data. For example, a model may cover a time horizon of multiple days but the behavior of certain model components may be the same for each day.
This case is illustrated in the following example, along with the appropriate idiom for encoding the repeating model behavior.

.. code-block:: c

  #TIMEHORIZON
  T = 5*24; // 5 days with hourly resolution
  #NODE factory
  #PARAMETERS
  production = import "production.csv"; // 24 values for hourly production
  #VARIABLES
  external : outflow[T];
  #CONSTRAINTS
  outflow[t] == production[mod(t,24)];
  #OBJECTIVES
  // objective definitions

Round Down Integer Division
===========================

Integer division is not natively implemented in GBOML but can be a very useful tool for many modeling tasks. To illustrate this, let us consider a model whose time horizon spans several days and some of whose components involve indices that correspond to hours and days, respectively. An example of such problems is given below with the appropriate idiom for encoding the different index behaviors.

.. code-block:: c

  #TIMEHORIZON
  T = 365*24; // 365 days with hourly resolution

  #GLOBAL
  days = T/24;

  #NODE bank
  #PARAMETERS
  interest_rate = import "interest_rate.csv"; // 365 values for daily interest rates
  mean_interest = sum(interest_rate[i] for i in [0:global.days-1])/global.days; // mean interest rate
  #VARIABLES
  internal : investment_interest[T];
  internal : investment[T];
  #CONSTRAINTS
  investment_interest[i] == interest_rate[(i-mod(i,24))/24]*investment[i] for i in [0:T-1];
