import type {
  SerializedOutlineItem,
  SerializedPreviewDocument,
} from "../transport/dto";

export type OutlineItem = SerializedOutlineItem;
export type PreviewDocument = SerializedPreviewDocument;

export const EMPTY_PREVIEW: PreviewDocument = {
  status: "empty",
  message: null,
  disclaimer: "结构预览不代表 Word 最终分页。",
  blocks: [],
};

export interface ContentSelection {
  selectionId: string;
  line: number | null;
}
