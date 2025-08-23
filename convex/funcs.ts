import { v } from "convex/values";
import { mutation } from "./_generated/server";

export const add_transcript = mutation({
  args: {
    connectionId: v.string(),
    transcript: v.string(),
  },
  handler: async (ctx, args) => {
    await ctx.db.insert("transcripts", {
      connectionId: args.connectionId,
      transcript: args.transcript,
    });
  },
});