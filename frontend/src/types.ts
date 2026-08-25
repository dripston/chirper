export interface PersonaSummary {
  id: string;
  name: string;
  ideology: string;
  engagement_style: any;
}

export interface PostReaction {
  hop: number;
  persona_id: string;
  persona_name: string;
  action: 'comment' | 'argue' | 'repost';
  text: string;
  drift_score_so_far?: number;
}

export interface DirectMessage {
  hop: number;
  persona_id: string;
  persona_name: string;
  text: string;
}

export interface DriftSummary {
  post_id: string;
  original_text: string;
  final_text: string;
  total_hops: number;
  total_reactions: number;
  reposts: number;
  comments: number;
  arguments: number;
  dms_sent: number;
  drift_score: number;
  drift_label: string;
  mvp_distorter: string;
  stop_reason: string;
}

export interface SimulationResult {
  post_id: string;
  original_text: string;
  final_text: string;
  feed: PostReaction[];
  dms: DirectMessage[];
  drift_summary: DriftSummary;
}

export type StreamEvent = 
  | { type: 'hop'; data: PostReaction }
  | { type: 'dm'; data: DirectMessage }
  | { type: 'done'; data: SimulationResult }
  | { type: 'entropy_update'; data: { hop: number; drift_score: number; drift_label: string } }
  | { type: 'error'; data: { message: string } };
