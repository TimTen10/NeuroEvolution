import numpy
import torch
import networks as nws
import random as rnd
import copy
import save_util as saveu
from statistics import mean

# TODO: delete population class, instead just have list

# function to input into the needed format
def clean_input(datasheet_path):
    test_data_file = open(f"{datasheet_path}", 'r')
    test_data_list = test_data_file.readlines()
    test_data_file.close()

    inputs = []
    targets = []
    # I want pairs: 784 pixel values, target
    for record in test_data_list:
        all_values = record.split(',')
        input = torch.zeros(28 * 28, dtype=torch.double)
        temp_var = (numpy.asfarray(all_values[1:]) / 255.0 * 0.99) + 0.01
        input = torch.add(input, torch.from_numpy(temp_var)).float()
        target = int(all_values[0])
        inputs.append(input)
        targets.append(target)

    return inputs, targets


# populates a population
def populate(population_size):
    population = []
    for i in range(population_size):
        population.append(nws.EvolutionNet())
    return population


# creates a new population
class nnPopulation:

    def __init__(self, population_size):
        self.population_size = population_size
        self.population = populate(population_size)


def fitness(network, inputs, targets):
    # best possible score 0.99
    score = 0
    for input, target in zip(inputs, targets):
        score += network.forward(input)[target].item()
    score /= len(inputs)

    return score


def evaluate_population(population, inputs, targets):
    results = []
    for network in population:
        results.append(fitness(network, inputs, targets))
    return results


def getNextParents(nets_and_results, keep, type='roulette_wheel'):
    # TODO: Add other types of selecting functions
    # e.g. Elitism, Tournament Selection, SUS

    # net_list should probably be a net and result list, since we need results too

    # Methode for roulette wheel: fitness ranges from 0 to 0.99
    # we take this score * 100 and turn it into an into
    # each individual gets slices equal to that number
    # then randomly select 'keep' many

    parent_nets = []
    net_list = [i[0] for i in nets_and_results]
    # fitness_scores is sorted, since we get a sorted list as input
    fitness_scores = [i[1] for i in nets_and_results]

    if type == 'roulette_wheel':
        roulette_wheel = []
        list_counter = 0

        for score in fitness_scores:
            slices = int(score * 100)
            for i in range(slices):
                roulette_wheel.append(list_counter)
            list_counter = list_counter + 1

        print(roulette_wheel)

        rnd.shuffle(roulette_wheel) # in place shuffle
        for i in range(keep):
            winner = rnd.randrange(len(roulette_wheel))
            parent_nets.append(net_list[roulette_wheel[winner]])

    return parent_nets

# TODO: make getNextParents more general and give it type as argument
# no if else needed afterwards
def evolve(population, train_inputs, train_targets, mutation_rate=0.07, keep=10, type='top'):
    """ First we apply the survival of the fittest principle """
    nets_and_results = list(zip(population, evaluate_population(population, train_inputs, train_targets)))
    # sort in place
    nets_and_results.sort(key=lambda x: x[1], reverse = True)

    if type == 'top':
        # since we sorted in place, new_nets is also sorted
        new_nets = [i[0] for i in nets_and_results]

        # get the size of the population to later repop it to the same size
        size = len(new_nets)

        # delete everything but the top 'keep' individuals
        # TODO: Maybe use a "getFittest" function here to select the parents
        del new_nets[keep:]

    elif type == 'roulette':

        new_nets = getNextParents(nets_and_results, keep=keep)
        size = len(nets_and_results)

    # fill the population back up to 'size'
    filler = []

    for i in range(len(new_nets)): # before 'keep'
        filler.append(copy.deepcopy(new_nets[i]))

    while len(new_nets) < size:
        new_nets.extend(copy.deepcopy(filler))

    """ After that we mutate the fittest individuals """
    # TODO: Write it, so it can be applied to any kind of neural network regardless of the layers
    # Look up Idealo Code, something with Parameter()
    for net in new_nets:
        #"""
        delta_fc1 = numpy.random.randn(*net.fc1.weight.data.size()).astype(numpy.float32) * numpy.array(mutation_rate).astype(numpy.float32)
        delta_fc1_tensor = torch.from_numpy(delta_fc1)
        net.fc1.weight.data = net.fc1.weight.data.add(delta_fc1_tensor)

        delta_fc2 = numpy.random.randn(*net.fc2.weight.data.size()).astype(numpy.float32) * numpy.array(mutation_rate).astype(numpy.float32)
        delta_fc2_tensor = torch.from_numpy(delta_fc2)
        net.fc2.weight.data = net.fc2.weight.data.add(delta_fc2_tensor)

        delta_fc3 = numpy.random.randn(*net.fc3.weight.data.size()).astype(numpy.float32) * numpy.array(mutation_rate).astype(numpy.float32)
        delta_fc3_tensor = torch.from_numpy(delta_fc3)
        net.fc3.weight.data = net.fc3.weight.data.add(delta_fc3_tensor)

        """
        mutation_vector_fc1 = torch.zeros(net.fc1.weight.data.size())
        for item in mutation_vector_fc1:
            item.add_((numpy.random.normal(0.0000, 0.008) if numpy.random.random() < mutation_rate else 0))
        net.fc1.weight.data = net.fc1.weight.data.add(mutation_vector_fc1)

        mutation_vector_fc2 = torch.zeros(net.fc2.weight.data.size())
        for item in mutation_vector_fc2:
            item.add_((numpy.random.normal(0.0000, 0.008) if numpy.random.random() < mutation_rate else 0))
        net.fc2.weight.data = net.fc2.weight.data.add(mutation_vector_fc2)

        mutation_vector_fc3 = torch.zeros(net.fc3.weight.data.size())
        for item in mutation_vector_fc3:
            item.add_((numpy.random.normal(0.0000, 0.012) if numpy.random.random() < mutation_rate else 0))
        net.fc3.weight.data = net.fc3.weight.data.add(mutation_vector_fc3)
        """
    return new_nets


def main():
    number_of_generations = 50
    size_of_population = 6
    mutation_rate = 0.05
    keep = 2
    results = []

    test_pop = nnPopulation(size_of_population)
    # training dataset
    train_inputs, train_targets = clean_input(datasheet_path="D:/workFolder/NeuroEvolution/mnist_dataset/mnist_train_100.txt")
    # validation dataset
    validate_inputs, validate_targets = clean_input(datasheet_path="D:/workFolder/NeuroEvolution/mnist_dataset/mnist_test.csv")

    gen_i = test_pop.population # = gen_0 aka initial population
    for i in range(number_of_generations + 1): # number of generations
        if i == 0:
            # initial generation only has to get evaluated
            gen_i_eval = sorted(evaluate_population(gen_i, train_inputs, train_targets), reverse = True)
            print(f"Gen {i}: {gen_i_eval}")
        else:
            # we need to evolve first if it's not the initial generation
            # the evolve turns the gen into the gen + 1 i.e. the new gen
            gen_i = evolve(gen_i, train_inputs, train_targets, mutation_rate=mutation_rate, keep=keep)

            gen_i_eval = sorted(evaluate_population(gen_i, train_inputs, train_targets), reverse = True)
            print(f"Gen {i}: {gen_i_eval}")

        gen_i_eval_result = [i] # Generation number
        gen_i_eval_result.extend(gen_i_eval) # Fitness Scores (best to worst)
        gen_i_eval_result.append(mean(gen_i_eval)) # Average
        results.append(gen_i_eval_result)

        if i == number_of_generations: # gens to test on vali
            gen_i_vali = sorted(evaluate_population(gen_i, validate_inputs, validate_targets), reverse = True)
            print(f"Validation Gen {i}: {gen_i_vali}")

            # TODO: add back later: gen_i_vali_result = [f'Validation Gen {i}']
            gen_i_vali_result = [-1]
            gen_i_vali_result.extend(gen_i_vali)
            gen_i_vali_result.append(mean(gen_i_vali))
            results.append(gen_i_vali_result)
            # ..._result is the string ready to add, the non ..._result version is the actual result list

    # save the results
    saveu.save_results(results)

    # TODO: Save more information into the result
    # e.g. Information on mutation rate, pop size, keep, number of generations

if __name__ == '__main__':
    main()
