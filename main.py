import GUI
import cProfile


def main():
    pr = cProfile.Profile()
    pr.enable()
    GUI.GUI()
    pr.disable()
    pr.print_stats(sort="cumulative")


main()
