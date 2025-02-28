import "express";

declare global {
  namespace Express {
    interface Request {
      session: import("supertokens-node/recipe/session").SessionContainer;
    }
  }
} 
