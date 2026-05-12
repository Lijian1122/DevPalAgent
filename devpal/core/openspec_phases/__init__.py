# -*- coding: utf-8 -*-
"""
OpenSpec 11 阶段工作流 - 模块化实现
"""

from .base import PhaseInterface, PhaseResult, OpenSpecContext
from .scheduler import OpenSpecPhaseScheduler
from .phase1_parse_requirements import Phase1ParseRequirements
from .phase2_create_structure import Phase2CreateStructure
from .phase3_technical_design import Phase3TechnicalDesign
from .phase4_generate_code import Phase4GenerateCode
from .phase5_generate_tests import Phase5GenerateTests
from .phase6_cmake_config import Phase6CMakeConfig
from .phase7_test_docs import Phase7TestDocs
from .phase8_readme import Phase8Readme
from .phase9_code_review import Phase9CodeReview
from .phase10_run_tests import Phase10RunTests
from .phase11_final_report import Phase11FinalReport

__all__ = [
    'PhaseInterface',
    'PhaseResult',
    'OpenSpecContext',
    'OpenSpecPhaseScheduler',
    'Phase1ParseRequirements',
    'Phase2CreateStructure',
    'Phase3TechnicalDesign',
    'Phase4GenerateCode',
    'Phase5GenerateTests',
    'Phase6CMakeConfig',
    'Phase7TestDocs',
    'Phase8Readme',
    'Phase9CodeReview',
    'Phase10RunTests',
    'Phase11FinalReport',
]
