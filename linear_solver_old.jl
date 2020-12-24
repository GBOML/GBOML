using Gurobi, JuMP

function lin_solve_aux( cost_vector::Array{Float64, 2},
                    constraint_matrix::Array{Float64, 2},
                    const_vector::Array{Float64, 2})::Array{Float64,2}

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

    # return the value
    return value.(x)
end

function lin_solve( cost_vector,
                    constraint_matrix,
                    const_vector)::Array{Float64,2}
    if typeof(cost_vector)==PyObject
        cost_vector = cost_vector.array
    end
    if typeof(constraint_matrix)== PyObject
        constraint_matrix = constraint_matrix.array
    end 
    if typeof(const_vector)==PyObject
        const_vector = const_vector.array
    end

    return lin_solve_aux(cost_vector,constraint_matrix,const_vector)
end

#constraint_matrix = [[1, 0, -1, 0] [0, 1, 0, -1.0]]
#const_vector = hcat([1, 1, 0, 0.0])
#cost_vector = hcat([1, 1.0])
#lin_solve(cost_vector, constraint_matrix, const_vector)
