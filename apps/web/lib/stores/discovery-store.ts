import { create } from 'zustand';
import type { ReviewStatus } from '@/lib/api/types';

interface DiscoveryState {
  selectedCandidateId: string | null;
  reviewFilter: ReviewStatus | 'all';
  searchQuery: string;
  reviewedIds: string[];
  setSelectedCandidate: (id: string | null) => void;
  setReviewFilter: (filter: ReviewStatus | 'all') => void;
  setSearchQuery: (query: string) => void;
  markReviewed: (id: string) => void;
}

export const useDiscoveryStore = create<DiscoveryState>()((set) => ({
  selectedCandidateId: null,
  reviewFilter: 'pending',
  searchQuery: '',
  reviewedIds: [],
  setSelectedCandidate: (id) => set({ selectedCandidateId: id }),
  setReviewFilter: (filter) => set({ reviewFilter: filter }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  markReviewed: (id) =>
    set((state) =>
      state.reviewedIds.includes(id)
        ? state
        : { reviewedIds: [...state.reviewedIds, id] }
    ),
}));
