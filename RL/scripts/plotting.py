import pandas as pd
import matplotlib.pyplot as plt
import os

os.makedirs('figures', exist_ok=True)

def save_plot(csv_file, title, xlabel, ylabel, filename, color='blue'):
    df = pd.read_csv(csv_file)
    plt.figure(figsize=(8, 5))
    plt.plot(df['Step'], df['Value'], color=color)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f'figures/{filename}.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved figures/{filename}.png")

save_plot('ep_rew_mean.csv', 
          'Mean Episode Reward', 
          'Timesteps', 'Reward', 
          'ep_rew_mean', color='blue')

save_plot('ep_len_mean.csv', 
          'Mean Episode Length', 
          'Timesteps', 'Steps', 
          'ep_len_mean', color='orange')

save_plot('success_rate.csv', 
          'Success Rate', 
          'Timesteps', 'Rate', 
          'success_rate', color='green')

save_plot('avg_final_distance.csv', 
          'Average Final Distance to Goal', 
          'Timesteps', 'Distance (m)', 
          'avg_final_distance', color='red')

save_plot('actor_loss.csv',
          'Actor Loss',
          'Timesteps', 'Loss',
          'actor_loss', color='purple')

save_plot('critic_loss.csv',
          'Critic Loss',
          'Timesteps', 'Loss',
          'critic_loss', color='darkblue')

save_plot('ent_coef.csv',
          'Entropy Coefficient',
          'Timesteps', 'Value',
          'ent_coef', color='brown')

save_plot('ent_coef_loss.csv',
          'Entropy Coefficient Loss',
          'Timesteps', 'Loss',
          'ent_coef_loss', color='olive')

save_plot('learning_rate.csv',
          'Learning Rate',
          'Timesteps', 'Learning Rate',
          'learning_rate', color='gray')

print("All figures saved to figures/ folder")