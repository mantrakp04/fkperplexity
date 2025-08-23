import { v } from "convex/values";
import { mutation, query } from "./_generated/server";
import { Id } from "./_generated/dataModel";

export const get_form = query({
  args: {
    formId: v.id("forms"),
  },
  handler: async (ctx, args) => {
    const userId = await ctx.auth.getUserIdentity();
    if (!userId) {
      throw new Error("User not authenticated");
    }

    const form = await ctx.db.get(args.formId);
    if (!form || form.userId !== userId.subject as Id<"users">) {
      throw new Error("Form not found or unauthorized");
    }

    return form;
  },
});

export const create_form = mutation({
  args: {
    callId: v.string(),
  },
  handler: async (ctx, args) => {
    const userId = await ctx.auth.getUserIdentity();
    if (!userId) {
      throw new Error("User not authenticated");
    }

    await ctx.db.insert("forms", {
      callId: args.callId,
      status: "in_progress",
      userId: userId.subject as Id<"users">,
    });

    // call action
  },
});

export const update_form_status = mutation({
  args: {
    formId: v.id("forms"),
    status: v.union(v.literal("in_progress"), v.literal("completed"), v.literal("failed"), v.literal("abandoned")),
  },
  handler: async (ctx, args) => {
    const userId = await ctx.auth.getUserIdentity();
    if (!userId) {
      throw new Error("User not authenticated");
    }

    const form = await ctx.db.get(args.formId);
    if (!form || form.userId !== userId.subject as Id<"users">) {
      throw new Error("Form not found or unauthorized");
    }

    await ctx.db.patch(args.formId, {
      status: args.status,
      ...(args.status === "completed" && { completedAt: new Date().toISOString() }),
    });
  },
});

export const add_transcript_chunk = mutation({
  args: {
    formId: v.id("forms"),
    chunk: v.string(),
  },
  handler: async (ctx, args) => {
    const userId = await ctx.auth.getUserIdentity();
    if (!userId) {
      throw new Error("User not authenticated");
    }

    const form = await ctx.db.get(args.formId);
    if (!form || form.userId !== userId.subject as Id<"users">) {
      throw new Error("Form not found or unauthorized");
    }

    await ctx.db.insert("transcripts", {
      formId: args.formId,
      chunk: args.chunk,
    });
  },
});

export const get_transcripts = query({
  args: {
    formId: v.id("forms"),
  },
  handler: async (ctx, args) => {
    const userId = await ctx.auth.getUserIdentity();
    if (!userId) {
      throw new Error("User not authenticated");
    }

    const form = await ctx.db.get(args.formId);
    if (!form || form.userId !== userId.subject as Id<"users">) {
      throw new Error("Form not found or unauthorized");
    }

    const transcripts = await ctx.db.query("transcripts").withIndex("by_form_id", (q) => q.eq("formId", args.formId)).collect();
    return transcripts.map((t) => t.chunk).join("\n");
  },
});
