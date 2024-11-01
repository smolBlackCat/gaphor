# This file is generated by coder.py. DO NOT EDIT!
# ruff: noqa: F401, E402, F811
# fmt: off

from __future__ import annotations

from gaphor.core.modeling.properties import (
    association,
    attribute as _attribute,
    derived,
    derivedunion,
    enumeration as _enumeration,
    redefine,
    relation_many,
    relation_one,
)


# 1: override Element
from gaphor.core.modeling.element import Element

# 4: override Diagram
from gaphor.core.modeling.diagram import Diagram

# 7: override Presentation
from gaphor.core.modeling.presentation import Presentation

class Comment(Element):
    annotatedElement: relation_many[Element]
    body: _attribute[str] = _attribute("body", str)


# 13: override StyleSheet
from gaphor.core.modeling.stylesheet import StyleSheet

class PendingChange(Element):
    applied: _attribute[int] = _attribute("applied", int, default=0)
    element_id: _attribute[str] = _attribute("element_id", str)
    op = _enumeration("op", ("add", "remove", "update"), "add")


class ElementChange(PendingChange):
    diagram_id: _attribute[str] = _attribute("diagram_id", str)
    element_name: _attribute[str] = _attribute("element_name", str)
    modeling_language: _attribute[str] = _attribute("modeling_language", str)


class ValueChange(PendingChange):
    property_name: _attribute[str] = _attribute("property_name", str)
    property_value: _attribute[str] = _attribute("property_value", str)


class RefChange(PendingChange):
    property_name: _attribute[str] = _attribute("property_name", str)
    property_ref: _attribute[str] = _attribute("property_ref", str)


class Picture(Element):
    content: _attribute[str] = _attribute("content", str)



Element.ownedElement = derivedunion("ownedElement", Element)
Element.owner = derivedunion("owner", Element, upper=1)
Element.presentation = association("presentation", Presentation, composite=True, opposite="subject")
Element.ownedDiagram = association("ownedDiagram", Diagram, composite=True, opposite="element")
Element.comment = association("comment", Comment, opposite="annotatedElement")
Element.ownedElement.add(Element.ownedDiagram)  # type: ignore[attr-defined]
Diagram.ownedPresentation = association("ownedPresentation", Presentation, composite=True, opposite="diagram")
Diagram.element = association("element", Element, upper=1, opposite="ownedDiagram")
Element.owner.add(Diagram.element)  # type: ignore[attr-defined]
Presentation.parent = association("parent", Presentation, upper=1, opposite="children")
Presentation.children = association("children", Presentation, composite=True, opposite="parent")
Presentation.diagram = association("diagram", Diagram, upper=1, opposite="ownedPresentation")
Presentation.subject = association("subject", Element, upper=1, opposite="presentation")
Comment.annotatedElement = association("annotatedElement", Element, opposite="comment")
