import { afterEach, describe, expect, it, vi } from "vitest";

describe("api client", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.resetModules();
  });

  it("createBrand posts to ingestion", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 202,
      json: async () => ({
        brand_id: "b1",
        status: "accepted",
        ingestion: "started",
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const { api } = await import("./client");
    const res = await api.createBrand({
      name: "Acme",
      primary_domain: "acme.com",
    });

    expect(res.brand_id).toBe("b1");
    expect(fetchMock).toHaveBeenCalledWith(
      "http://ingestion.test/brands",
      expect.objectContaining({ method: "POST" })
    );
  });

  it("getTriggers returns empty export on 404", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        statusText: "Not Found",
        text: async () => "",
      })
    );

    const { api } = await import("./client");
    const exp = await api.getTriggers("brand-x");
    expect(exp.triggers).toEqual([]);
    expect(exp.brand_id).toBe("brand-x");
  });

  it("startAnalysis posts to analysis service", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 202,
      json: async () => ({ brand_id: "b1", status: "accepted" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const { api } = await import("./client");
    await api.startAnalysis("b1");
    expect(fetchMock).toHaveBeenCalledWith(
      "http://analysis.test/brands/b1/analyze",
      expect.objectContaining({ method: "POST" })
    );
  });
});
