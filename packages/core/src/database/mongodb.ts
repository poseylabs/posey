import { MongoClient, Db, MongoClientOptions, ObjectId } from 'mongodb';
import { DatabaseAdapter } from './adapter';

import { ConversationThread, Message } from '../types';

const fallbackConnectionString = 'mongodb://localhost:27017/posey';

export class MongoDBAdapter implements DatabaseAdapter {
  private readonly client: MongoClient;
  private db: Db | null = null;

  constructor() {

    const MONGODB_URI = process.env.MONGODB_CONNECTION_STRING || fallbackConnectionString;

    const isLocal = process.env.NODE_ENV === 'development';
    const options: MongoClientOptions = {
      serverSelectionTimeoutMS: 5000,
      socketTimeoutMS: 45000,
      ssl: !isLocal, // Disable SSL for local development
    };
    this.client = new MongoClient(MONGODB_URI, options);
  }

  async connect(): Promise<void> {
    try {
      await this.client.connect();
      this.db = this.client.db();
    } catch (error) {
      console.error('Failed to connect to MongoDB:', error);
      throw error;
    }
  }

  async disconnect(): Promise<void> {
    await this.client.close();
  }

  getDatabase(): Db {
    if (!this.db) {
      throw new Error('Database not connected. Call connect() first.');
    }
    return this.db;
  }

  async getAllConversations() {
    const collection = this.db?.collection('conversations');
    if (!collection) {
      throw new Error('Collection not found');
    }
    return await collection.find({}).toArray();
  }

  async saveConversation(conversation: ConversationThread) {
    const collection = this.db?.collection('conversations');
    if (!collection) {
      throw new Error('Collection not found');
    }
    return await collection.insertOne(conversation);
  }

  async saveMessage(message: Message) {
    const collection = this.db?.collection('messages');
    if (!collection) {
      throw new Error('Collection not found');
    }
    return await collection.insertOne(message);
  }

  async updateConversation(id: string, updates: Partial<ConversationThread>) {
    const collection = this.db?.collection('conversations');
    if (!collection) {
      throw new Error('Collection not found');
    }
    return await collection.updateOne({ _id: new ObjectId(id) }, { $set: updates });
  }

}
