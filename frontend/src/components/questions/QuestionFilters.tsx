import { Search, Filter, X, SlidersHorizontal, ChevronDown } from 'lucide-react';
import { useState, useEffect, useRef } from 'react';
import { cn } from '../../lib/utils';

export interface QuestionFiltersState {
  category: string;
  difficulty: string;
  search: string;
  company: string;
}

interface QuestionFiltersProps {
  filters: QuestionFiltersState;
  onFilterChange: (filters: QuestionFiltersState) => void;
  companyOptions?: string[];
  totalCount?: number;
  filteredCount?: number;
}

const categoryOptions = [
  { value: '', label: 'All Categories' },
  { value: 'behavioral', label: 'Behavioral' },
  { value: 'technical', label: 'Technical' },
  { value: 'system_design', label: 'System Design' },
];

const difficultyOptions = [
  { value: '', label: 'All Levels' },
  { value: 'easy', label: 'Easy' },
  { value: 'medium', label: 'Medium' },
  { value: 'hard', label: 'Hard' },
];

// Chip button component for filter options
function FilterChip({
  label,
  isActive,
  onClick,
  variant = 'default',
}: {
  label: string;
  isActive: boolean;
  onClick: () => void;
  variant?: 'default' | 'category' | 'company' | 'easy' | 'medium' | 'hard';
}) {
  const variantStyles = {
    default: isActive
      ? 'bg-electric-blue text-white border-electric-blue'
      : 'bg-[hsl(var(--muted)/0.5)] text-text-secondary border-[hsl(var(--border))] hover:border-electric-blue/50 hover:text-text-primary',
    category: isActive
      ? 'bg-blue-500 text-white border-blue-500'
      : 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/30 hover:bg-blue-500/20',
    company: isActive
      ? 'bg-orange-500 text-white border-orange-500'
      : 'bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-500/30 hover:bg-orange-500/20',
    // Semantic difficulty colors matching card badges
    easy: isActive
      ? 'bg-emerald-500 text-white border-emerald-500'
      : 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/20',
    medium: isActive
      ? 'bg-amber-500 text-white border-amber-500'
      : 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30 hover:bg-amber-500/20',
    hard: isActive
      ? 'bg-red-500 text-white border-red-500'
      : 'bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/30 hover:bg-red-500/20',
  };

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'px-3 py-1.5 rounded-full text-sm font-medium border transition-all',
        'active:scale-95 whitespace-nowrap',
        variantStyles[variant]
      )}
    >
      {label}
    </button>
  );
}

export default function QuestionFilters({
  filters,
  onFilterChange,
  companyOptions = [],
}: QuestionFiltersProps) {
  const [localSearch, setLocalSearch] = useState(filters.search);
  const [isExpanded, setIsExpanded] = useState(false);
  const filterRef = useRef<HTMLDivElement>(null);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      if (localSearch !== filters.search) {
        onFilterChange({ ...filters, search: localSearch });
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [localSearch, filters, onFilterChange]);

  // Close on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (filterRef.current && !filterRef.current.contains(event.target as Node)) {
        setIsExpanded(false);
      }
    }
    if (isExpanded) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isExpanded]);

  const handleCategoryChange = (category: string) => {
    onFilterChange({ ...filters, category });
  };

  const handleDifficultyChange = (difficulty: string) => {
    onFilterChange({ ...filters, difficulty });
  };

  const handleCompanyChange = (company: string) => {
    onFilterChange({ ...filters, company });
  };

  const handleClearFilters = () => {
    setLocalSearch('');
    onFilterChange({
      category: '',
      difficulty: '',
      search: '',
      company: '',
    });
  };

  const activeFilterCount = [
    filters.category,
    filters.difficulty,
    filters.company,
  ].filter(Boolean).length;

  const hasActiveFilters = activeFilterCount > 0 || filters.search;

  return (
    <div ref={filterRef} className="mb-6 space-y-3">
      {/* Search Bar Row */}
      <div className="flex gap-2">
        {/* Search Input */}
        <div className="flex-1 relative group">
          <Search
            size={18}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary group-focus-within:text-electric-blue transition-colors"
          />
          <input
            type="text"
            placeholder="Search questions..."
            value={localSearch}
            onChange={(e) => setLocalSearch(e.target.value)}
            className="input w-full pl-10 pr-10 h-11"
          />
          {localSearch && (
            <button
              onClick={() => setLocalSearch('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-full text-text-tertiary hover:text-text-primary hover:bg-[hsl(var(--muted))] transition-colors"
              aria-label="Clear search"
            >
              <X size={16} />
            </button>
          )}
        </div>

        {/* Filter Toggle Button */}
        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          className={cn(
            'flex items-center gap-2 px-4 h-11 rounded-xl border font-medium transition-all',
            'active:scale-95',
            isExpanded || activeFilterCount > 0
              ? 'bg-electric-blue text-white border-electric-blue'
              : 'bg-[hsl(var(--card))] text-text-secondary border-[hsl(var(--border))] hover:border-electric-blue/50'
          )}
        >
          <SlidersHorizontal size={18} />
          <span className="hidden sm:inline">Filters</span>
          {activeFilterCount > 0 && (
            <span className="flex items-center justify-center w-5 h-5 text-xs font-bold rounded-full bg-white/20">
              {activeFilterCount}
            </span>
          )}
          <ChevronDown
            size={16}
            className={cn(
              'transition-transform duration-200',
              isExpanded && 'rotate-180'
            )}
          />
        </button>

        {/* Clear Button (visible when filters active) */}
        {hasActiveFilters && (
          <button
            type="button"
            onClick={handleClearFilters}
            className="flex items-center gap-1.5 px-3 h-11 rounded-xl text-text-tertiary hover:text-status-error hover:bg-status-error/10 transition-colors"
            aria-label="Clear all filters"
          >
            <X size={18} />
            <span className="hidden sm:inline text-sm font-medium">Clear</span>
          </button>
        )}
      </div>

      {/* Expandable Filter Panel */}
      <div
        className={cn(
          'overflow-hidden transition-all duration-300 ease-out',
          isExpanded ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
        )}
      >
        <div className="bg-[hsl(var(--card))] border border-[hsl(var(--border))] rounded-2xl p-4 space-y-4">
          {/* Category Filter */}
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Category
            </label>
            <div className="flex flex-wrap gap-2">
              {categoryOptions.map((opt) => (
                <FilterChip
                  key={opt.value}
                  label={opt.label}
                  isActive={filters.category === opt.value}
                  onClick={() => handleCategoryChange(opt.value)}
                  variant="category"
                />
              ))}
            </div>
          </div>

          {/* Difficulty Filter */}
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Difficulty
            </label>
            <div className="flex flex-wrap gap-2">
              {difficultyOptions.map((opt) => (
                <FilterChip
                  key={opt.value}
                  label={opt.label}
                  isActive={filters.difficulty === opt.value}
                  onClick={() => handleDifficultyChange(opt.value)}
                  variant={opt.value === '' ? 'default' : (opt.value as 'easy' | 'medium' | 'hard')}
                />
              ))}
            </div>
          </div>

          {/* Company Filter (if options available) */}
          {companyOptions.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">
                Company
              </label>
              <div className="flex flex-wrap gap-2 max-h-24 overflow-y-auto">
                <FilterChip
                  label="All Companies"
                  isActive={!filters.company}
                  onClick={() => handleCompanyChange('')}
                  variant="company"
                />
                {companyOptions.slice(0, 10).map((company) => (
                  <FilterChip
                    key={company}
                    label={company}
                    isActive={filters.company === company}
                    onClick={() => handleCompanyChange(company)}
                    variant="company"
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Active Filters Pills (below search when collapsed) */}
      {!isExpanded && hasActiveFilters && (
        <div className="flex flex-wrap items-center gap-2">
          <Filter size={14} className="text-text-tertiary" />
          {filters.category && (
            <button
              type="button"
              onClick={() => handleCategoryChange('')}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20 hover:bg-blue-500/20 transition-colors group"
            >
              {categoryOptions.find((c) => c.value === filters.category)?.label}
              <X size={12} className="opacity-50 group-hover:opacity-100" />
            </button>
          )}
          {filters.difficulty && (
            <button
              type="button"
              onClick={() => handleDifficultyChange('')}
              className={cn(
                'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-colors group',
                filters.difficulty === 'easy' && 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20 hover:bg-emerald-500/20',
                filters.difficulty === 'medium' && 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20 hover:bg-amber-500/20',
                filters.difficulty === 'hard' && 'bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20 hover:bg-red-500/20'
              )}
            >
              {difficultyOptions.find((d) => d.value === filters.difficulty)?.label}
              <X size={12} className="opacity-50 group-hover:opacity-100" />
            </button>
          )}
          {filters.company && (
            <button
              type="button"
              onClick={() => handleCompanyChange('')}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/20 hover:bg-orange-500/20 transition-colors group"
            >
              {filters.company}
              <X size={12} className="opacity-50 group-hover:opacity-100" />
            </button>
          )}
          {filters.search && (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-[hsl(var(--muted))] text-text-secondary border border-[hsl(var(--border))]">
              <Search size={12} />
              "{filters.search.length > 15 ? filters.search.slice(0, 15) + '...' : filters.search}"
            </span>
          )}
        </div>
      )}
    </div>
  );
}
