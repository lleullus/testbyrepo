import { beforeEach, describe, expect, test, vi } from "vitest";
import {
  supportsProjectSidebarNavigation,
  tryNavigateToProjectHomeViaSidebar,
} from "../../src/browser/pageActions.js";
import type { ChromeClient } from "../../src/browser/types.js";

const logger = vi.fn();
const PROJECT_URL = "https://chatgpt.com/g/g-p-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-prom/project";

beforeEach(() => {
  logger.mockClear();
});

describe("project sidebar navigation", () => {
  test("recognizes only slugged ChatGPT project-home URLs", () => {
    expect(supportsProjectSidebarNavigation(PROJECT_URL)).toBe(true);
    expect(
      supportsProjectSidebarNavigation(
        "https://chatgpt.com/g/g-p-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/project",
      ),
    ).toBe(false);
    expect(
      supportsProjectSidebarNavigation(
        "https://chatgpt.com/g/g-p-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-prom/c/thread",
      ),
    ).toBe(false);
  });

  test("clicks the matching project home and waits for the SPA route to settle", async () => {
    const runtime = {
      evaluate: vi
        .fn()
        .mockResolvedValueOnce({
          result: { value: { status: "clicked", projectName: "prom" } },
        })
        .mockResolvedValueOnce({
          result: { value: { href: PROJECT_URL, title: "ChatGPT - prom" } },
        }),
    } as unknown as ChromeClient["Runtime"];

    await expect(tryNavigateToProjectHomeViaSidebar(runtime, PROJECT_URL, logger)).resolves.toBe(
      true,
    );
    expect(runtime.evaluate).toHaveBeenCalledTimes(2);
    expect(logger).toHaveBeenCalledWith("[nav] project home opened through ChatGPT sidebar (prom)");
  });
});
