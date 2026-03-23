import { Search, Filter, X } from 'lucide-react';
import { useState, useEffect } from 'react';

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
}

const categoryOptions = [
  { value: '', label: 'All Categories' },
  { value: 'behavioral', label: 'Behavioral' },
  { value: 'technical', label: 'Technical' },
  { value: 'system_design', label: 'System Design' },
];

const difficultyOptions = [
  { value: '', label: 'All Difficulties' },
  { value: 'easy', label: 'Easy' },
  { value: 'medium', label: 'Medium' },
  { value: 'hard', label: 'Hard' },
];

export default function QuestionFilters({
  filters,
  onFilterChange,
  companyOptions = [],
}: QuestionFiltersProps) {
  const [localSearch, setLocalSearch] = useState(filters.search);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      if (localSearch !== filters.search) {
        onFilterChange({ ...filters, search: localSearch });
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [localSearch, filters, onFilterChange]);

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

  const hasActiveFilters =
    filters.category || filters.difficulty || filters.search || filters.company;

  return (
    <div className="card p-4 mb-6">
      <div className="flex flex-wrap gap-4">
        {/* Search */}
        <div className="flex-1 min-w-[200px]">
          <div className="relative">
            <Search
              size={18}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary"
            />
            <input
              type="text"
              placeholder="Search questions..."
              value={localSearch}
              onChange={(e) => setLocalSearch(e.target.value)}
              className="input pl-10 w-full"
            />
          </div>
        </div>

        {/* Category Filter */}
        <div className="w-[180px]">
          <select
            value={filters.category}
            onChange={(e) => handleCategoryChange(e.target.value)}
            className="input w-full"
          >
            {categoryOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Difficulty Filter */}
        <div className="w-[160px]">
          <select
            value={filters.difficulty}
            onChange={(e) => handleDifficultyChange(e.target.value)}
            className="input w-full"
          >
            {difficultyOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Company Filter */}
        {companyOptions.length > 0 && (
          <div className="w-[180px]">
            <select
              value={filters.company}
              onChange={(e) => handleCompanyChange(e.target.value)}
              className="input w-full"
            >
              <option value="">All Companies</option>
              {companyOptions.map((company) => (
                <option key={company} value={company}>
                  {company}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Clear Filters */}
        {hasActiveFilters && (
          <button
            onClick={handleClearFilters}
            className="btn-ghost flex items-center gap-2 text-text-secondary"
          >
            <X size={16} />
            Clear
          </button>
        )}
      </div>

      {/* Active Filters Display */}
      {hasActiveFilters && (
        <div className="flex items-center gap-2 mt-3 pt-3 border-t border-border-light">
          <Filter size={14} className="text-text-tertiary" />
          <span className="text-sm text-text-tertiary">Active filters:</span>
          {filters.category && (
            <span className="badge badge-outline text-xs">
              {categoryOptions.find((c) => c.value === filters.category)?.label}
            </span>
          )}
          {filters.difficulty && (
            <span className="badge badge-outline text-xs">
              {difficultyOptions.find((d) => d.value === filters.difficulty)?.label}
            </span>
          )}
          {filters.company && (
            <span className="badge badge-outline text-xs">{filters.company}</span>
          )}
          {filters.search && (
            <span className="badge badge-outline text-xs">"{filters.search}"</span>
          )}
        </div>
      )}
    </div>
  );
}
