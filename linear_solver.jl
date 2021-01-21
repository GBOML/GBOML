using Gurobi, JuMP

function lin_solve( cost_vector::Array{Float64, 2},
                    constraint_matrix::Array{Float64, 2},
                    const_vector::Array{Float64, 2})

    # get the dimensions
    nb_const, nb_var = size(constraint_matrix)

    # instantiate an optimization model
    model = Model(Gurobi.Optimizer)

    # create the varoables of the problem
    @variable(model, x[1:nb_var, 1:1])

    # create the constraints
    @constraint(model, constraint_matrix * x .<= const_vector)

    # create the objective
    @objective(model, Min, sum(cost_vector .* x))

    # solve
    optimize!(model)

    #ADD unbounded
    #Terminate before optimal -> Time limit check 
    #Distinguish btw suboptimal and feasible
    #infeasible / unbounded / error
    if termination_status(model) == MOI.OPTIMAL
        optimal_solution = value.(x)
        optimal_objective = objective_value(model)
        s = "Optimal"

    elseif termination_status(model) == MOI.INFEASIBLE 
        optimal_solution = Float64[]
        optimal_objective = Float64[]
        s = "Infeasible"

    elseif termination_status(model) == MOI.INFEASIBLE_OR_UNBOUNDED
        optimal_solution = Float64[]
        optimal_objective = Float64[]
        s = "Infeasible_or_Unbounded"

    elseif termination_status(model) == MOI.ALMOST_OPTIMAL
        optimal_solution = value.(x)
        optimal_objective = objective_value(model)
        s = "Almost_Optimal"

    elseif termination_status(model) == MOI.ITERATION_LIMIT || termination_status(model) == MOI.TIME_LIMIT ||
        termination_status(model) == MOI.NODE_LIMIT || termination_status(model) == MOI.SOLUTION_LIMIT ||
        termination_status(model) == MOI.MEMORY_LIMIT || termination_status(model) == MOI.OBJECTIVE_LIMIT ||
        termination_status(model) == MOI.NORM_LIMIT || termination_status(model) == MOI.OTHER_LIMIT
        optimal_solution = Float64[]
        optimal_objective = Float64[]
        s = "User_Limit"
    else
        optimal_solution = Float64[]
        optimal_objective = Float64[]
        s = "Error"
    end

    # return the value
    return optimal_solution, optimal_objective,s
end

function lin_solve_sparse(  cost_vector::Array{Float64, 2},
                            constraint_matrix::Array{Float64, 2},
                            const_vector::Array{Float64, 2})
    """The second array has as shape (N, 3) where N is the number of nonzero
       elements in the constraint matrix A. The array contains triplets
       (i, j, v) where (i, j) is the position of the value v in the matrix A.
       Additionally, this array is sorted according to the first column.
       WARNING: indexing starts from 1"""

   # get the dimensions
   nb_const = size(const_vector)[1]
   nb_var = size(cost_vector)[1]

   # instantiate an optimization model
   model = Model(Gurobi.Optimizer)

   # create the varoables of the problem
   @variable(model, x[1:nb_var, 1:1])

   # create the constraints
   begin_pt = 1
   end_pt = 1

   while begin_pt <= size(constraint_matrix)[2]
       # find the part of the array relative to one line in the matrix A
       end_pt = begin_pt
       line_id = convert(Int64, constraint_matrix[1,begin_pt])
       # find the last element relative to line 'line_id'
       while end_pt <= size(constraint_matrix)[2] && constraint_matrix[1, end_pt] == line_id
           end_pt += 1
       end

       end_pt -=1

       # create the constraint
       var_indices = convert(Array{Int64}, constraint_matrix[2,begin_pt:end_pt])
       var_coef = constraint_matrix[3,begin_pt:end_pt]
       @constraint(model, sum(var_coef .* x[var_indices, 1]) <= const_vector[line_id, 1])
       begin_pt = end_pt+1
   end

   # create the objective
   @objective(model, Min, sum(cost_vector .* x))

   # solve
   optimize!(model)

   if termination_status(model) == MOI.OPTIMAL
    optimal_solution = value.(x)
    optimal_objective = objective_value(model)
    s = "Optimal"

    elseif termination_status(model) == MOI.INFEASIBLE 
        optimal_solution = Float64[]
        optimal_objective = Float64[]
        s = "Infeasible"

    elseif termination_status(model) == MOI.INFEASIBLE_OR_UNBOUNDED
        optimal_solution = Float64[]
        optimal_objective = Float64[]
        s = "Infeasible_or_Unbounded"

    elseif termination_status(model) == MOI.ALMOST_OPTIMAL
        optimal_solution = value.(x)
        optimal_objective = objective_value(model)
        s = "Almost_Optimal"

    elseif termination_status(model) == MOI.ITERATION_LIMIT || termination_status(model) == MOI.TIME_LIMIT ||
        termination_status(model) == MOI.NODE_LIMIT || termination_status(model) == MOI.SOLUTION_LIMIT ||
        termination_status(model) == MOI.MEMORY_LIMIT || termination_status(model) == MOI.OBJECTIVE_LIMIT ||
        termination_status(model) == MOI.NORM_LIMIT || termination_status(model) == MOI.OTHER_LIMIT
        optimal_solution = Float64[]
        optimal_objective = Float64[]
        s = "User_Limit"
    else
        optimal_solution = Float64[]
        optimal_objective = Float64[]
        s = "Error"
    end


   # return the value
   return optimal_solution, optimal_objective,s

end


#constraint_matrix = [[1, 0, -1, 0] [0, 1, 0, -1.0]]
#const_vector = hcat([1, 1, 0, 0.0])
#cost_vector = hcat([1, 1.0])
#lin_solve(cost_vector, constraint_matrix, const_vector)

#constraint_matrix_sparse = [[1, 2, 3, 4] [1, 2, 1, 2] [1, 1, -1, -1.0]]
#lin_solve_sparse(cost_vector, constraint_matrix_sparse, const_vector)
