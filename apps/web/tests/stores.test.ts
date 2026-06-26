import { describe, it, expect, beforeEach } from 'vitest';
import { useFilterStore } from '@/lib/stores/filter-store';
import { useSelectionStore } from '@/lib/stores/selection-store';
import { useMapStore } from '@/lib/stores/map-store';
import { ZHAMBYL_CENTER } from '@/lib/constants';

describe('useFilterStore', () => {
  beforeEach(() => {
    useFilterStore.getState().resetFilters();
  });

  it('has all filters null in initial state', () => {
    const state = useFilterStore.getState();
    expect(state.district).toBeNull();
    expect(state.basin).toBeNull();
    expect(state.type).toBeNull();
    expect(state.condition).toBeNull();
    expect(state.inspectionStatus).toBeNull();
  });

  it('setFilter updates the specified filter', () => {
    useFilterStore.getState().setFilter('district', 'Test District');
    expect(useFilterStore.getState().district).toBe('Test District');
  });

  it('setFilter can set each filter independently', () => {
    useFilterStore.getState().setFilter('basin', 'р. Талас');
    useFilterStore.getState().setFilter('type', 'dam');
    useFilterStore.getState().setFilter('condition', 'critical');
    useFilterStore.getState().setFilter('inspectionStatus', 'overdue');
    const state = useFilterStore.getState();
    expect(state.basin).toBe('р. Талас');
    expect(state.type).toBe('dam');
    expect(state.condition).toBe('critical');
    expect(state.inspectionStatus).toBe('overdue');
  });

  it('resetFilters clears all filters to null', () => {
    useFilterStore.getState().setFilter('district', 'Test');
    useFilterStore.getState().setFilter('condition', 'normal');
    useFilterStore.getState().resetFilters();
    const state = useFilterStore.getState();
    expect(state.district).toBeNull();
    expect(state.condition).toBeNull();
  });
});

describe('useSelectionStore', () => {
  beforeEach(() => {
    useSelectionStore.getState().setSelectedId(null);
  });

  it('has selectedId null in initial state', () => {
    expect(useSelectionStore.getState().selectedId).toBeNull();
  });

  it('setSelectedId updates the selected ID', () => {
    useSelectionStore.getState().setSelectedId('KZ-ZH-0001');
    expect(useSelectionStore.getState().selectedId).toBe('KZ-ZH-0001');
  });

  it('setSelectedId(null) clears the selection', () => {
    useSelectionStore.getState().setSelectedId('KZ-ZH-0001');
    useSelectionStore.getState().setSelectedId(null);
    expect(useSelectionStore.getState().selectedId).toBeNull();
  });
});

describe('useMapStore', () => {
  beforeEach(() => {
    useMapStore.getState().setViewport({ ...ZHAMBYL_CENTER });
  });

  it('initial viewport matches ZHAMBYL_CENTER', () => {
    const viewport = useMapStore.getState().viewport;
    expect(viewport.longitude).toBe(ZHAMBYL_CENTER.longitude);
    expect(viewport.latitude).toBe(ZHAMBYL_CENTER.latitude);
    expect(viewport.zoom).toBe(ZHAMBYL_CENTER.zoom);
  });

  it('setViewport updates the viewport', () => {
    useMapStore.getState().setViewport({ longitude: 71.0, latitude: 43.0, zoom: 9 });
    const viewport = useMapStore.getState().viewport;
    expect(viewport.longitude).toBe(71.0);
    expect(viewport.latitude).toBe(43.0);
    expect(viewport.zoom).toBe(9);
  });
});
