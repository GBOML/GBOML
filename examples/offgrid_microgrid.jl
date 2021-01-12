using JuMP
using Gurobi
using Plots

# DEFINE PARAMETERS

# TIME DATA
n_d = 4;
dT = 1;
T = 24*dT*n_d;
time = [t for t = 1:T];

# ECONOMIC DATA
n_y = 2;
rate = 0.07;
c_S = 1;
c_B = 1;
f = rate * ((1+rate)^n_y) / (((1+rate)^n_y) - 1);
C_S = c_S * f;
C_B = c_B * f;
C_L = 10;

# TECHNICAL DATA
#C = Dict([(1, 6.9), (2, 6.4), (3, 6.1), (4, 5.9), (5, 5.7), (6, 5.4), (7, 4.8), (8, 4.5), (9, 4.6),
#          (10, 4.6), (11, 4.7), (12, 4.9), (13, 5.1), (14, 5.3), (15, 5.4), (16, 5.4), (17, 5.4), (18, 5.8),
#          (19, 8.4), (20, 10.6), (21, 11.0), (22, 10.5), (23, 9.2), (24, 7.8)])
#pi_S = Dict([(1,0), (2,0), (3,0), (4,0) , (5,0), (6,0), (7,0), (8,0), (9,0), (10,0.04), (11,0.08), (12, 0.12),
#            (13, 0.14), (14, 0.15), (15, 0.14), (16, 0.12), (17, 0.08), (18, 0.04), (19, 0), (20, 0), (21, 0),
#            (22, 0), (23, 0), (24, 0)])
C_d = [6.9,6.4,6.1,5.9,5.7,5.4,4.8,4.5,4.6,4.6,4.7,4.9,5.1,5.3,5.4,5.4,5.4,5.8, 8.4,10.6,11.0,10.5,9.2,7.8];
pi_S_d = [0,0,0,0,0,0,0,0,0,0.04,0.08,0.12,0.14,0.15, 0.14,0.12,0.08,0.04,0,0,0,0,0,0];
C_v, pi_S_v = [], [];
for d = 1:n_d
    global C_v = vcat(C_v, C_d);
    global pi_S_v = vcat(pi_S_v, pi_S_d);
end

C = Dict(time .=> C_v);
pi_S = Dict(time .=> pi_S_v);

# CREATE EMPTY MODEL

LP_model = Model(Gurobi.Optimizer)

# ADD VARIABLES

@variable(LP_model, 0 <= P_S[1:T])
@variable(LP_model, 0 <= K_S)
@variable(LP_model, 0 <= L[1:T])
@variable(LP_model, P_B[1:T])
@variable(LP_model, 0 <= E_B[1:T])
@variable(LP_model, 0 <= S_B)

# ADD CONSTRAINTS

@constraint(LP_model, power_balance[t = 1:T], P_S[t] - P_B[t] + L[t] == C[t])
@constraint(LP_model, solar_PV_production[t = 1:T], P_S[t] == pi_S[t] * K_S)
@constraint(LP_model, battery_storage_dynamics[t = 1:T-1], E_B[t+1] == E_B[t] + P_B[t]*dT)
@constraint(LP_model, battery_storage_initialization, E_B[1] == S_B/2)
@constraint(LP_model, battery_max_state_of_charge[t = 1:T], E_B[t] <= S_B)

# ADD OBJECTIVE

@objective(LP_model, Min, (C_S * K_S + C_B * S_B)/T + C_L * sum(L))

# WRITE MODEL TO FILE

#write_to_file(LP_model, "model.mps")

# SOLVE MODEL

optimize!(LP_model)

# PLOTTING

fig = plot(time, [value.(P_B), value.(P_S), C_v],label = ["battery" "pv_production" "consumption"]);
savefig(fig, "test_1.pdf");
