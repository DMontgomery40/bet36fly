import type { Metrics } from './types';

const shuffledKey = 'shuffled_readout_labels_on_trained_wiring';
const legacyShuffledKey = 'shuffled_training_labels';
const names: Record<string, string> = {
  train_frequency_prior: 'Training frequency prior',
  pregame_feature_logistic: 'Pregame feature logistic',
  frozen_connectome_trained_readout: 'Frozen wiring + trained readout',
  [shuffledKey]: 'Shuffled readout labels',
  silenced_connectome_fixed_readout: 'Silenced wiring + fixed readout',
};

export function controlRows(controls: Record<string, Record<string, Metrics>>) {
  return Object.entries(controls)
    .filter(([key]) => key !== legacyShuffledKey || !(shuffledKey in controls))
    .map(([sourceKey, metrics]) => {
      const key = sourceKey === legacyShuffledKey ? shuffledKey : sourceKey;
      return {
        key,
        label: names[key] || key.replaceAll('_', ' '),
        metrics,
        description: key === shuffledKey
          ? 'Only final readout labels are shuffled; wiring trained on true labels stays fixed for this control.'
          : undefined,
      };
    });
}
