import { create } from "zustand";

import {
  controllerApi,
  type ControllerPageContext,
  type ControllerSession,
  type ControllerStreamEvent,
  type ControllerTurn,
  type NeedsTarget,
} from "../api/controller";

export interface StreamState {
  thinking: string;
  answer: string;
  tools: string[];
  active: boolean;
}

interface ControllerState {
  session: ControllerSession | null;
  open: boolean;
  busy: boolean;
  error: string | null;
  pendingUser: string | null;
  stream: StreamState | null;
  needsTarget: NeedsTarget | null;
  /** 确认/完成一轮后自增，工作台与项目页据此重拉数据。 */
  dataVersion: number;
  ensureSession: () => Promise<ControllerSession | null>;
  refresh: () => Promise<void>;
  send: (text: string, context: ControllerPageContext) => Promise<void>;
  confirm: (decision: "confirm" | "cancel") => Promise<ControllerTurn | null>;
  setOpen: (open: boolean) => void;
}

let inFlight: Promise<ControllerSession> | null = null;

export const useControllerStore = create<ControllerState>((set, get) => {
  function applyEvent(event: ControllerStreamEvent) {
    if (event.type === "user") {
      set((state) => {
        const current = state.session;
        if (!current) return { pendingUser: null };
        if (current.messages.some((row) => row.id === event.message.id)) {
          return { pendingUser: null };
        }
        return {
          pendingUser: null,
          session: { ...current, messages: [...current.messages, event.message] },
        };
      });
      return;
    }
    if (event.type === "thinking") {
      set((state) =>
        state.stream
          ? { stream: { ...state.stream, thinking: state.stream.thinking + event.text } }
          : {},
      );
      return;
    }
    if (event.type === "delta") {
      set((state) =>
        state.stream
          ? { stream: { ...state.stream, answer: state.stream.answer + event.text } }
          : {},
      );
      return;
    }
    if (event.type === "tool") {
      if (event.status !== "running") return;
      set((state) =>
        state.stream
          ? { stream: { ...state.stream, tools: [...state.stream.tools, event.name].slice(-3) } }
          : {},
      );
      return;
    }
    if (event.type === "done") {
      set((state) => ({
        session: event.turn.session,
        pendingUser: null,
        stream: null,
        busy: false,
        needsTarget: event.turn.needs_target ?? null,
        dataVersion: state.dataVersion + 1,
      }));
      return;
    }
    if (event.type === "error") {
      set({ error: event.detail, stream: null, busy: false });
      void get().refresh();
    }
  }

  return {
    session: null,
    open: false,
    busy: false,
    error: null,
    pendingUser: null,
    stream: null,
    needsTarget: null,
    dataVersion: 0,

    ensureSession: async () => {
      const existing = get().session;
      if (existing) return existing;
      if (inFlight) return inFlight;
      inFlight = controllerApi
        .createSession()
        .then((session) => {
          set({ session });
          return session;
        })
        .catch((reason: unknown) => {
          set({
            error: reason instanceof Error ? reason.message : "总控初始化失败",
          });
          throw reason;
        })
        .finally(() => {
          inFlight = null;
        });
      return inFlight;
    },

    refresh: async () => {
      const current = get().session;
      if (!current) {
        void get().ensureSession();
        return;
      }
      try {
        const next = await controllerApi.getSession(current.id);
        set({ session: next });
      } catch {
        // reset/迁移后旧会话已不存在：清掉并重新 get-or-create。
        set({ session: null });
        void get().ensureSession();
      }
    },

    send: async (text, context) => {
      const session = get().session ?? (await get().ensureSession());
      if (!session || get().busy) return;
      const message = text.trim().slice(0, 2000);
      if (!message) return;
      set({
        busy: true,
        error: null,
        pendingUser: message,
        stream: { thinking: "", answer: "", tools: [], active: true },
        needsTarget: null,
      });
      let finished = false;
      try {
        await controllerApi.streamMessage(session.id, message, context, (event) => {
          if (event.type === "done" || event.type === "error") finished = true;
          applyEvent(event);
        });
      } catch (reason: unknown) {
        set({ error: reason instanceof Error ? reason.message : "总控没有回应" });
      } finally {
        if (!finished) {
          set((state) => ({
            busy: false,
            stream: null,
            error: state.error ?? "连接中断，已保留你的消息；请再发一次或刷新页面。",
          }));
          void get().refresh();
        }
      }
    },

    confirm: async (decision) => {
      const session = get().session;
      if (!session?.pending_action_json || get().busy) return null;
      set({ busy: true, error: null });
      try {
        const turn = await controllerApi.confirm(
          session.id,
          session.pending_action_json.id,
          decision,
        );
        set((state) => ({
          session: turn.session,
          pendingUser: null,
          stream: null,
          needsTarget: turn.needs_target ?? null,
          dataVersion: state.dataVersion + 1,
        }));
        return turn;
      } catch (reason: unknown) {
        set({ error: reason instanceof Error ? reason.message : "确认失败" });
        return null;
      } finally {
        set({ busy: false });
      }
    },

    setOpen: (open) => {
      set({ open });
      if (open) void get().ensureSession();
    },
  };
});
