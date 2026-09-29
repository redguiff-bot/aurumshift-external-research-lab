import * as restate from "@restatedev/restate-sdk";
import fs from "node:fs";
const LOG = process.env.SIDE_LOG || "/tmp/lab/work/restate/sidefx.log";
const app = (line) => fs.appendFileSync(LOG, line + "\n");
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
// attempt counters live in-process only (lost on kill) -> we log every execution instead
let attemptCounter = {};

const agent = restate.workflow({
  name: "Agent",
  handlers: {
    run: async (ctx, task) => {
      const id = ctx.key;
      const work = await ctx.run("work", async () => {
        attemptCounter[id] = (attemptCounter[id] || 0) + 1;
        app(`WORK_START,${id},${attemptCounter[id]},${process.pid},${Date.now()}`);
        await sleep(3000);
        app(`WORK_END,${id},${attemptCounter[id]},${process.pid},${Date.now()}`);
        return { task: id, result: `result-of-${id}`, pid: process.pid };
      });
      const review = await ctx.run("review", async () => {
        app(`REVIEW,${id},${work.result},${process.pid},${Date.now()}`);
        return { ok: true, reviewed: work.result };
      });
      return { id, work, review };
    },
  },
});

// Scenario B: flaky step
const flaky = restate.service({
  name: "Flaky",
  handlers: {
    // fails first 3 executions of the run-closure, custom retry policy 
    transient: async (ctx, failN) => {
      return ctx.run("flaky-step", async () => {
        const n = ((attemptCounter["fl"] = (attemptCounter["fl"] || 0) + 1));
        app(`FLAKY,${n},${process.pid},${Date.now()}`);
        if (n <= failN) throw new Error("transient boom " + n);
        return "ok after " + n;
      }, { initialRetryInterval: { milliseconds: 1000 }, retryIntervalFactor: 2, maxRetryAttempts: 100 });
    },
    // always fails; ctx.run policy: max 4 attempts -> TerminalError
    terminal: async (ctx) => {
      return ctx.run("always-fail", async () => {
        app(`TERM,${process.pid},${Date.now()}`);
        throw new Error("always boom");
      }, { initialRetryInterval: { milliseconds: 500 }, retryIntervalFactor: 2, maxRetryAttempts: 4 });
    },
    // plain throw in handler, server default retry policy (500ms x2, max 1m, 70 attempts then pause)
    defaultpolicy: async (ctx) => {
      app(`DEFPOL,${process.pid},${Date.now()}`);
      throw new Error("handler boom");
    },
  },
});

restate.serve({ services: [agent, flaky], port: 55414 });
