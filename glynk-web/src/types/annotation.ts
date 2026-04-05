export interface Annotation {
  annotation_id?: string;
  content_id: string;
  type: string;
  text: string;
  note?: string;
  color?: string;
  location?: string;
  created_at?: string;
  updated_at?: string;
}

export interface QueryResult {
  annotation: Annotation;
  score?: number;
  content_title?: string;
}

export interface QueryResponse {
  results: QueryResult[];
  total: number;
}
