import io_data
import tensorflow as tf
from model.inception_cnn import (make_model, MODEL_SAVE_PATH_WITHOUT_EXTENSION, load_model, remove_model, save_model)


train_x_data, train_y_data, test_x_data, test_y_data = io_data.get_train_test_data(one_hot=True)
train_data_len = len(train_x_data)
test_data_len = len(test_x_data)
print(train_data_len, test_data_len)

X = tf.placeholder("float", [None, 225])
Y = tf.placeholder("float", [None, 225])

dropout_rate = tf.placeholder("float")

model = make_model(X, dropout_rate)
model_with_softmax = tf.cast(tf.nn.softmax(tf.cast(model, tf.float64)), tf.float32)  # SUCCESS
#model_with_softmax = tf.nn.softmax(model)  # FAIL

# cross entropy
cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(model, Y))

LEARNING_RATE = 0.001
learning_rate = tf.Variable(LEARNING_RATE)
optimizer = tf.train.RMSPropOptimizer(LEARNING_RATE, 0.9)
train = optimizer.minimize(cost)

init = tf.initialize_all_variables()

with tf.Session() as sess:

    """
        Variables and functions about
        Loading and Saving Data.
    """

    import os
    saver = tf.train.Saver()
    INFO_FILE_PATH = MODEL_SAVE_PATH_WITHOUT_EXTENSION + ".info"

    def do_load():
        start_epoch = 1
        try:
            epochs = []
            avg_costs = []
            avg_accuracys = []
            learning_rates = []

            with open(INFO_FILE_PATH, "r") as f:
                while True:
                    line = f.readline()
                    if not line:
                        break
                    data = line.split()
                    epochs.append(int(data[0]))
                    avg_costs.append(float(data[1]))
                    avg_accuracys.append(float(data[2]))
                    learning_rates.append(float(data[3]))
            load_model(sess, saver)
            print("[*] The save file exists!")

            print("Do you wanna continue? (y/n) ", end="", flush=True)
            if input() == 'n':
                print("not continue...")
                print("[*] Start a training from the beginning.")
                os.remove(INFO_FILE_PATH)
                remove_model()
                sess.run(init)
            else:
                print("continue...")
                print("[*] Start a training from the save file.")
                start_epoch = epochs[-1] + 1
                for epoch, avg_cost, avg_accuracy, learning_rate in zip(epochs, avg_costs, avg_accuracys,
                                                                        learning_rates):
                    print("Epoch {0} with learning rate = {1} : avg_cost = {2}, avg_accuracy = {3}".
                          format(epoch, learning_rate, avg_cost, avg_accuracy))

        except FileNotFoundError:
            print("[*] There is no save files.")
            print("[*] Start a training from the beginning.")
            sess.run(init)

        return start_epoch

    def do_save():
        print("[progress] Saving result! \"Never\" exit!!", end='', flush=True)
        save_model(sess, saver)
        with open(INFO_FILE_PATH, "a") as f:
            f.write("{0} {1} {2} {3}".format(epoch, avg_cost, avg_accuracy, LEARNING_RATE) + os.linesep)
        print("", end='\r', flush=True)


    """
        Variables and functions about
        Training and Testing Model
    """
    DISPLAY_SAVE_STEP = 1
    TRAINING_EPOCHS = 10000
    BATCH_SIZE = 512

    def do_train():
        print("[progress] Training model for optimizing cost!", end='', flush=True)
        # Loop all batches for training
        avg_cost = 0
        for start in range(0, train_data_len, BATCH_SIZE):
            end = min(start + BATCH_SIZE, train_data_len)
            batch_x = train_x_data[start:end]
            batch_y = train_y_data[start:end]
            data = {X: batch_x, Y: batch_y, dropout_rate: 0.5}
            sess.run(train, feed_dict=data)
            avg_cost += sess.run(cost, feed_dict=data) * len(batch_x) / train_data_len

        print("", end='\r', flush=True)
        return avg_cost

    def do_test():
        print("[progress] Testing model for evaluating accuracy!", end='', flush=True)
        correct_prediction = tf.equal(tf.argmax(model_with_softmax, 1), tf.argmax(Y, 1))
        accuracy = tf.reduce_mean(tf.cast(correct_prediction, "float"))

        # Loop all batches for test
        avg_accuracy = 0
        for start in range(0, test_data_len, BATCH_SIZE):
            end = min(start + BATCH_SIZE, test_data_len)
            batch_x = test_x_data[start:end]
            batch_y = test_y_data[start:end]
            data = {X: batch_x, Y: batch_y, dropout_rate: 1.0}
            avg_accuracy += accuracy.eval(data) * len(batch_x) / test_data_len

        print("", end='\r', flush=True)
        return avg_accuracy


    ################################## Start of flow ##################################

    start_epoch = do_load()

    if start_epoch == 1:
        avg_accuracy = do_test()
        print("After initializing, accuracy = {0}".format(avg_accuracy))

    # Training cycle
    for epoch in range(start_epoch, TRAINING_EPOCHS + 1):

        avg_cost = do_train()

        # Logging the result
        if epoch % DISPLAY_SAVE_STEP == start_epoch % DISPLAY_SAVE_STEP or epoch == TRAINING_EPOCHS:
            avg_accuracy = do_test()
            do_save()

            # Print Result
            print("Epoch {0} : avg_cost = {1}, accuracy = {2}".format(epoch, avg_cost, avg_accuracy))
