import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, FlatList } from 'react-native';
import axios from 'axios';
import { API_URL } from '@env';

interface PredictionResponse {
  numbers: number[];
  probabilities: Record<string, number>;
}

const PredictionView: React.FC = () => {
  const [data, setData] = useState<PredictionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPredictions = async () => {
      try {
        const response = await axios.get<PredictionResponse>(API_URL);
        setData(response.data);
      } catch (err) {
        console.error('API call failed:', err);
        setError('Failed to fetch predictions. Check the console for more details.');
      } finally {
        setLoading(false);
      }
    };

    fetchPredictions();
  }, []);

  if (loading) {
    return <ActivityIndicator size="large" style={styles.centered} />;
  }

  if (error) {
    return <Text style={styles.error}>{error}</Text>;
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Lotto Predictions</Text>
      {data && (
        <>
          <Text style={styles.subtitle}>Top 5 Numbers:</Text>
          <Text style={styles.numbers}>{data.numbers.join(', ')}</Text>
          <Text style={styles.subtitle}>Probabilities:</Text>
          <FlatList
            data={Object.entries(data.probabilities)}
            keyExtractor={(item) => item[0]}
            renderItem={({ item }) => (
              <Text style={styles.probabilityItem}>
                {item[0]}: {item[1]}
              </Text>
            )}
          />
        </>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: '#f5f5f5',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
  },
  subtitle: {
    fontSize: 18,
    fontWeight: '600',
    marginTop: 15,
  },
  numbers: {
    fontSize: 18,
    textAlign: 'center',
    marginVertical: 10,
  },
  error: {
    color: 'red',
    textAlign: 'center',
    marginTop: 20,
  },
  probabilityItem: {
    fontSize: 16,
    paddingVertical: 5,
  },
});

export default PredictionView;
