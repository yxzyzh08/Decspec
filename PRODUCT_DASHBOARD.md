# DevSpec Product Dashboard

> **Generated At**: 2025-12-07 15:08:06
> **Phase**: 0 (Genesis Spec)

## Progress Overview

| Dimension | Progress | Detail |
| :--- | :--- | :--- |
| **Schema Compliance** | `[####################]` 100% | 57/57 files |
| **Spec Sync** | `[###################-]` 95% | 61/64 nodes |
| **Feature Assignment** | `[####################]` 100% | 17/17 features |
| **Overall** | `[###################-]` 98% | Weighted: Schema(30%) + Spec(30%) + Assignment(40%) |

---

## Schema Validation Results

| File | Type | Status | Issues |
| :--- | :--- | :--- | :--- |
| `.specgraph\product.yaml` | product | O Valid | - |
| `.specgraph\components\comp_cli_app.yaml` | component | O Valid | - |
| `.specgraph\components\comp_cli_context.yaml` | component | O Valid | - |
| `.specgraph\components\comp_cli_debug_logger.yaml` | component | O Valid | - |
| `.specgraph\components\comp_cli_init.yaml` | component | O Valid | - |
| `.specgraph\components\comp_cli_monitor.yaml` | component | O Valid | - |
| `.specgraph\components\comp_cli_sync.yaml` | component | O Valid | - |
| `.specgraph\components\comp_cli_validate_prd.yaml` | component | O Valid | - |
| `.specgraph\components\comp_config_manager.yaml` | component | O Valid | - |
| `.specgraph\components\comp_consistency_monitor.yaml` | component | O Valid | - |
| `.specgraph\components\comp_context_assembler.yaml` | component | O Valid | - |
| `.specgraph\components\comp_error_handler.yaml` | component | ! Warnings | [W] file_path: Code file does not exist: devspec/infra/errors.py |
| `.specgraph\components\comp_frontend_component_library.yaml` | component | O Valid | - |
| `.specgraph\components\comp_graph_database.yaml` | component | O Valid | - |
| `.specgraph\components\comp_graph_query.yaml` | component | O Valid | - |
| `.specgraph\components\comp_graph_sync.yaml` | component | O Valid | - |
| `.specgraph\components\comp_logger_factory.yaml` | component | O Valid | - |
| `.specgraph\components\comp_markdown_parser.yaml` | component | O Valid | - |
| `.specgraph\components\comp_prd_validator.yaml` | component | O Valid | - |
| `.specgraph\components\comp_specview_graph_renderer.yaml` | component | O Valid | - |
| `.specgraph\components\comp_specview_routes.yaml` | component | O Valid | - |
| `.specgraph\components\comp_specview_search_engine.yaml` | component | O Valid | - |
| `.specgraph\components\comp_specview_server.yaml` | component | O Valid | - |
| `.specgraph\components\comp_specview_templates.yaml` | component | O Valid | - |
| `.specgraph\components\comp_spec_indexer.yaml` | component | O Valid | - |
| `.specgraph\components\comp_yaml_schema_validator.yaml` | component | O Valid | - |
| `.specgraph\design\des_architecture.yaml` | design | O Valid | - |
| `.specgraph\design\des_bootstrap_strategy.yaml` | design | O Valid | - |
| `.specgraph\design\des_documentation.yaml` | design | O Valid | - |
| `.specgraph\design\des_domain_model.yaml` | design | O Valid | - |
| `.specgraph\design\des_frontend_design.yaml` | design | O Valid | - |
| `.specgraph\design\des_interaction.yaml` | design | O Valid | - |
| `.specgraph\design\des_knowledge_classification.yaml` | design | O Valid | - |
| `.specgraph\design\des_philosophy.yaml` | design | O Valid | - |
| `.specgraph\design\des_safety.yaml` | design | O Valid | - |
| `.specgraph\design\des_specgraph_schema.yaml` | design | O Valid | - |
| `.specgraph\design\des_tech_strategy.yaml` | design | O Valid | - |
| `.specgraph\features\feat_cli_command_structure.yaml` | feature | O Valid | - |
| `.specgraph\features\feat_code_scanner.yaml` | feature | O Valid | - |
| `.specgraph\features\feat_config_management.yaml` | feature | O Valid | - |
| `.specgraph\features\feat_consistency_monitor.yaml` | feature | O Valid | - |
| `.specgraph\features\feat_context_assembler.yaml` | feature | O Valid | - |
| `.specgraph\features\feat_error_handling.yaml` | feature | O Valid | - |
| `.specgraph\features\feat_frontend_component_library.yaml` | feature | O Valid | - |
| `.specgraph\features\feat_logging.yaml` | feature | O Valid | - |
| `.specgraph\features\feat_quality_prd_validator.yaml` | feature | O Valid | - |
| `.specgraph\features\feat_requirement_collector.yaml` | feature | O Valid | - |
| `.specgraph\features\feat_specgraph_database.yaml` | feature | O Valid | - |
| `.specgraph\features\feat_specgraph_engine.yaml` | feature | O Valid | - |
| `.specgraph\features\feat_specview_dashboard_core.yaml` | feature | O Valid | - |
| `.specgraph\features\feat_specview_design_view.yaml` | feature | O Valid | - |
| `.specgraph\features\feat_specview_hierarchy_view.yaml` | feature | O Valid | - |
| `.specgraph\features\feat_specview_relation_view.yaml` | feature | O Valid | - |
| `.specgraph\features\feat_specview_search.yaml` | feature | O Valid | - |
| `.specgraph\substrate\sub_coding_style.yaml` | substrate | O Valid | - |
| `.specgraph\substrate\sub_frontend_style.yaml` | substrate | O Valid | - |
| `.specgraph\substrate\sub_tech_stack.yaml` | substrate | O Valid | - |

---

## System Design (Domain & Design)

| Node ID | Type | Spec Status |
| :--- | :--- | :--- |
| `des_architecture` | Design | O Synced |
| `des_bootstrap_strategy` | Design | X YAML Only |
| `des_documentation` | Design | O Synced |
| `des_domain_model` | Design | O Synced |
| `des_frontend_design` | Design | O Synced |
| `des_interaction` | Design | O Synced |
| `des_knowledge_classification` | Design | O Synced |
| `des_philosophy` | Design | O Synced |
| `des_safety` | Design | O Synced |
| `des_specgraph_schema` | Design | O Synced |
| `des_tech_strategy` | Design | X YAML Only |
| `dom_cli` | Domain | O Synced |
| `dom_core` | Domain | O Synced |
| `dom_frontend` | Domain | O Synced |
| `dom_infra` | Domain | O Synced |
| `dom_quality` | Domain | O Synced |
| `dom_specview` | Domain | O Synced |
| `prod_devspec` | Product | O Synced |
| `sub_coding_style` | Substrate | X YAML Only |
| `sub_frontend_style` | Substrate | O Synced |
| `sub_meta_schema` | Substrate | O Synced |
| `sub_tech_stack` | Substrate | O Synced |

---

## Features

| Node ID | Domain | Spec Status | Assignment Status |
| :--- | :--- | :--- | :--- |
| `feat_cli_command_structure` | dom_cli | O Synced | O Assigned (5) |
| `feat_code_scanner` | dom_core | O Synced | O Assigned (1) |
| `feat_config_management` | dom_infra | O Synced | O Assigned (1) |
| `feat_consistency_monitor` | dom_core | O Synced | O Assigned (4) |
| `feat_context_assembler` | dom_core | O Synced | O Assigned (2) |
| `feat_error_handling` | dom_infra | O Synced | O Assigned (1) |
| `feat_frontend_component_library` | dom_frontend | O Synced | O Assigned (1) |
| `feat_logging` | dom_infra | O Synced | O Assigned (2) |
| `feat_quality_prd_validator` | dom_quality | O Synced | O Assigned (1) |
| `feat_requirement_collector` | dom_core | O Synced | O Assigned (3) |
| `feat_specgraph_database` | dom_core | O Synced | O Assigned (3) |
| `feat_specgraph_engine` | dom_core | O Synced | O Assigned (1) |
| `feat_specview_dashboard_core` | dom_specview | O Synced | O Assigned (3) |
| `feat_specview_design_view` | dom_specview | O Synced | O Assigned (2) |
| `feat_specview_hierarchy_view` | dom_specview | O Synced | O Assigned (2) |
| `feat_specview_relation_view` | dom_specview | O Synced | O Assigned (2) |
| `feat_specview_search` | dom_specview | O Synced | O Assigned (2) |

---

## Components

| Node ID | Parent Feature | Spec Status |
| :--- | :--- | :--- |
| `comp_cli_app` | feat_cli_command_structure | O Synced |
| `comp_cli_context` | feat_context_assembler, feat_requirement_collector | O Synced |
| `comp_cli_debug_logger` | feat_logging | O Synced |
| `comp_cli_init` | feat_cli_command_structure, feat_requirement_collector | O Synced |
| `comp_cli_monitor` | feat_cli_command_structure | O Synced |
| `comp_cli_sync` | feat_cli_command_structure | O Synced |
| `comp_cli_validate_prd` | feat_cli_command_structure | O Synced |
| `comp_config_manager` | feat_config_management | O Synced |
| `comp_consistency_monitor` | feat_consistency_monitor | O Synced |
| `comp_context_assembler` | feat_context_assembler, feat_requirement_collector | O Synced |
| `comp_error_handler` | feat_error_handling | O Synced |
| `comp_frontend_component_library` | feat_frontend_component_library | O Synced |
| `comp_graph_database` | feat_specgraph_database | O Synced |
| `comp_graph_query` | feat_specgraph_database | O Synced |
| `comp_graph_sync` | feat_specgraph_database | O Synced |
| `comp_logger_factory` | feat_logging | O Synced |
| `comp_markdown_parser` | feat_consistency_monitor | O Synced |
| `comp_prd_validator` | feat_quality_prd_validator | O Synced |
| `comp_spec_indexer` | feat_code_scanner, feat_consistency_monitor, feat_specgraph_engine | O Synced |
| `comp_specview_graph_renderer` | feat_specview_relation_view | O Synced |
| `comp_specview_routes` | feat_specview_dashboard_core, feat_specview_design_view, feat_specview_hierarchy_view, feat_specview_relation_view, feat_specview_search | O Synced |
| `comp_specview_search_engine` | feat_specview_search | O Synced |
| `comp_specview_server` | feat_specview_dashboard_core | O Synced |
| `comp_specview_templates` | feat_specview_dashboard_core, feat_specview_design_view, feat_specview_hierarchy_view | O Synced |
| `comp_yaml_schema_validator` | feat_consistency_monitor | O Synced |

---
*Auto-generated by DevSpec Consistency Monitor*
