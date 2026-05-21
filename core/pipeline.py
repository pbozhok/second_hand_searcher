"""
Module Pipeline for the second-hand research agent.

Provides a modular, extensible pipeline that processes queries through
a series of modules (scrapers, filters, processors, reviewers).
"""

import asyncio
from typing import List, Dict, Any, Optional, Callable, Type
from dataclasses import dataclass, field

from core.module import Module, ModuleType, PipelineContext, PipelineError
from core.registry import ModuleRegistry, registry as global_registry
from core.logging import get_logger

logger = get_logger(__name__, module_name="core.pipeline")


@dataclass
class PipelineConfig:
    """Configuration for the pipeline execution."""
    query: str
    max_results: int = 20
    target_currency: str = "EUR"
    llm_backend: str = "gemini"
    skip_preprocess: bool = False
    skip_filter: bool = False
    skip_score: bool = False
    skip_reviews: bool = False
    debug: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for PipelineContext."""
        return {
            "query": self.query,
            "max_results": self.max_results,
            "target_currency": self.target_currency,
            "llm_backend": self.llm_backend,
            "skip_preprocess": self.skip_preprocess,
            "skip_filter": self.skip_filter,
            "skip_score": self.skip_score,
            "skip_reviews": self.skip_reviews,
            "debug": self.debug,
        }


class Pipeline:
    """
    Orchestrates the execution of modules in the research pipeline.
    
    The pipeline processes a query through these stages:
    1. Pre-processing (optional): Query cleaning and keyword generation
    2. Scraping: Fetch listings from multiple platforms
    3. Processing: Price conversion, model extraction, description fetching
    4. Filtering: Keyword or LLM-based relevance filtering
    5. Scoring: LLM-based ranking
    6. Review aggregation: Fetch and summarize reviews
    
    Each stage is implemented by one or more modules.
    """
    
    def __init__(self, registry: Optional[ModuleRegistry] = None):
        """
        Initialize the pipeline.
        
        Args:
            registry: Module registry to use (defaults to global registry)
        """
        self.registry = registry or global_registry
        self._modules: Dict[ModuleType, List[Module]] = {}
    
    def load_modules(self) -> None:
        """Load all modules from the registry."""
        self._modules = {}
        for module_type in ModuleType:
            modules = self.registry.get_modules(module_type)
            if modules:
                self._modules[module_type] = modules
    
    async def execute(self, config: PipelineConfig) -> PipelineContext:
        """
        Execute the full pipeline with the given configuration.
        
        Args:
            config: Pipeline configuration
            
        Returns:
            PipelineContext with all results and metadata
        """
        # Create initial context
        context = PipelineContext(
            query=config.query,
            listings=[],
            config=config.to_dict(),
            errors=[],
            metadata={"pipeline_start": "start"}
        )
        
        logger.info("Pipeline started", extra={"query": config.query, "config": config.to_dict()})
        
        try:
            # Load modules if not already loaded
            if not self._modules:
                self.load_modules()
            
            # Stage 1: Scraping
            context = await self._execute_stage(ModuleType.SCRAPER, context)
            logger.info("Scraping complete", extra={"listing_count": len(context.listings)})
            
            # Stage 2: Processing (price conversion, etc.)
            context = await self._execute_stage(ModuleType.PROCESSOR, context)
            logger.info("Processing complete", extra={"listing_count": len(context.listings)})
            
            # Stage 3: Filtering
            if not config.skip_filter:
                context = await self._execute_stage(ModuleType.FILTER, context)
                logger.info("Filtering complete", extra={"listing_count": len(context.listings)})
            
            # Stage 4: Scoring/Ranking
            if not config.skip_score:
                context = await self._execute_stage(ModuleType.RANKER, context)
                logger.info("Scoring complete", extra={"listing_count": len(context.listings)})
            
            # Stage 5: Review aggregation
            if not config.skip_reviews:
                context = await self._execute_stage(ModuleType.REVIEWER, context)
                logger.info("Review aggregation complete", extra={"listing_count": len(context.listings)})
            
            logger.info("Pipeline completed successfully", 
                       extra={"listing_count": len(context.listings), "error_count": len(context.errors)})
            
        except Exception as e:
            logger.error("Pipeline failed", extra={"error": str(e)})
            context.add_error(
                module_name="pipeline",
                error_type="PIPELINE_ERROR",
                message=str(e)
            )
        
        return context
    
    async def _execute_stage(self, module_type: ModuleType, context: PipelineContext) -> PipelineContext:
        """
        Execute all modules of a specific type.
        
        Args:
            module_type: The type of modules to execute
            context: The pipeline context
            
        Returns:
            Updated pipeline context
        """
        modules = self._modules.get(module_type, [])
        
        if not modules:
            logger.debug("No modules for stage", stage=module_type.value)
            return context
        
        logger.info("Executing stage", extra={"stage": module_type.value, "module_count": len(modules)})
        
        # Execute all modules of this type
        for module in modules:
            try:
                logger.debug("Executing module", extra={"module_name": module.name, "module_type": module.module_type.value})
                
                # Initialize module if not already done
                if not hasattr(module, '_initialized') or not module._initialized:
                    module.initialize(context.config)
                
                # Execute the module
                context = await module.execute(context)
                
                logger.debug("Module completed", extra={"module_name": module.name, "listing_count": len(context.listings), "error_count": len(context.errors)})
                
            except Exception as e:
                logger.error("Module failed", extra={"module_name": module.name, "error": str(e)})
                context.add_error(
                    module_name=module.name,
                    error_type=f"{module.module_type.value}_ERROR",
                    message=str(e),
                    severity="ERROR"
                )
        
        return context
    
    async def execute_module(self, module: Module, context: PipelineContext) -> PipelineContext:
        """
        Execute a single module.
        
        Args:
            module: The module to execute
            context: The pipeline context
            
        Returns:
            Updated pipeline context
        """
        logger.debug("Executing single module", module_name=module.name)
        
        try:
            # Initialize if needed
            if not hasattr(module, '_initialized') or not module._initialized:
                module.initialize(context.config)
            
            context = await module.execute(context)
            
        except Exception as e:
            logger.error("Module execution failed", module_name=module.name, error=str(e))
            context.add_error(
                module_name=module.name,
                error_type=f"{module.module_type.value}_ERROR",
                message=str(e)
            )
        
        return context


def create_pipeline(config: Optional[PipelineConfig] = None) -> Pipeline:
    """
    Factory function to create a pipeline with optional configuration.
    
    Args:
        config: Optional pipeline configuration
        
    Returns:
        Configured Pipeline instance
    """
    return Pipeline()
