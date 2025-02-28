const { ApolloServer, gql } = require('apollo-server');

// Define your schema
const typeDefs = gql`
  type Query {
    hello: String
    getTask(taskId: ID!): Task
  }

  type Task {
    id: ID
    name: String
    status: String
  }
`;

// Define your resolvers
const resolvers = {
  Query: {
    hello: () => 'Hello world!',
    getTask: (_, { taskId }) => {
      return { id: taskId, name: "Sample Task", status: "Pending" };
    },
  },
};

// Create the Apollo Server
const server = new ApolloServer({ typeDefs, resolvers });

// Start the server
server.listen().then(({ url }) => {
  console.info(`🚀 Server ready at ${url}`);
});
