import client from './client';

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
    const response = await client.get<QuizQuestion[]>('/quiz/generate', {
      timeout: 60000,
    });
    return response.data;
  },
};

export const QuotesAPI = {
  getRandomQuote: async (): Promise<Quote> => {
    const response = await client.get<Quote>('/quotes/random');
    return response.data;
  },
};
