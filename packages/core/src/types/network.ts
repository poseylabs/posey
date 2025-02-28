export interface FetchResponse {
  ok: boolean;
  json: () => Promise<any>;
  status?: number;
}

export interface JsonFetchResponse {
  data: any;
  metadata: any;
  status?: number;
}
