import { Component, type ReactNode } from "react";

interface SceneBoundaryState {
  hasError: boolean;
}

export class SceneBoundary extends Component<{ children: ReactNode }, SceneBoundaryState> {
  state: SceneBoundaryState = { hasError: false };

  static getDerivedStateFromError(): SceneBoundaryState {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex h-full items-center justify-center bg-paper p-6">
          <div className="card max-w-sm p-6 text-center">
            <div className="font-display text-xl text-ink">3D 场景没有启动</div>
            <p className="mt-2 text-xs leading-6 text-ink-muted">
              浏览器可能不支持 WebGL，或显卡上下文暂时丢失。流水线、审核和溯源页不受影响。
            </p>
            <button
              type="button"
              onClick={() => this.setState({ hasError: false })}
              className="mt-4 rounded-control bg-apple px-4 py-2 text-xs font-medium text-white transition-colors hover:bg-apple-hover"
            >
              重试 3D
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
