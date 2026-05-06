import aiml
import time

if not hasattr(time, "clock"):
    time.clock = time.perf_counter
    
# Função para carregar o arquivo AIML com base no passo
def load_aiml_for_step(step, kernel):
    try:
        file_name = f"book_bot/step{step}.aiml"  # Constrói o nome do arquivo com base no step
        kernel.learn(file_name)
    except:
        pass

# Inicializa o bot no passo 0
def initialize_aiml_engine():
    kernel = aiml.Kernel()
    return kernel
