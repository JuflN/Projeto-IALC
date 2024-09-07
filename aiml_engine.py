import aiml

def initialize_aiml_engine():
    kernel = aiml.Kernel()
    kernel.learn("/home/jufln/Projeto-IALC/book_bot.aiml")
    return kernel
