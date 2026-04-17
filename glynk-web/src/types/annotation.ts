/**
 * Anchor metadata contains the positioning info for highlights.
 * This replaces the old TextSelectionAnchor.
 */
export interface AnchorMetadata {
  type?: string;             // 'text_selection' | 'text'
  spans?: string[];
  startSpanId?: string;
  endSpanId?: string;
  startOffset?: number;
  endOffset?: number;
  color?: string;            // 'yellow' | 'green' | 'blue' | 'pink' | 'ghost'
  note?: string;
  [key: string]: unknown;
}

/**
 * Annotation as returned by the API.
 * Backend formats anchors into this compat shape.
 */
export interface Annotation {
  id: string;
  content_id: string;        // target_unit
  anchor: AnchorMetadata;    // anchor metadata (color, spans, offsets)
  type: string;              // role: see backend ROLE_SCHEMAS — highlight | hook | note | summary | reply | like | bookmark | follow
  text: string;              // source unit body.html
  tags: string[];
  contextuality: string;
  source: string;
  visibility: string;
  created_at?: string;
  // Extra fields from new model
  target_span?: string;
  source_unit?: string;
  author_name?: string;
  author_id?: string;
  content_title?: string;
}

// Keep TextSelectionAnchor as alias for compat
export type TextSelectionAnchor = AnchorMetadata;
