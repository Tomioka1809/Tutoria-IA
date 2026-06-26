import client, { API_URL } from './client';

export interface QuizQuestion {
  question: string;
  options: string[];
  correctAnswerIndex: number;
  explanation: string;
}

export interface Quote {
  id: number;
  text: string;
}

export const QuizAPI = {
  generateQuiz: async (): Promise<QuizQuestion[]> => {
    // LLM generation takes time, override default 5s timeout by using fetch directly
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000); // 60s timeout
    
    try {
      const response = await fetch(`${API_URL}/quiz/generate`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          // Note: Add Authorization header here if needed in the future
        },
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      return data;
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  }
};

export const QuotesAPI = {
  getRandomQuote: async (): Promise<Quote> => {
    const response = await client.get('/quotes/random');
    return response.data;
  }
};
