from easul.visual import element as E, render as R, Visual
# from easul.visual import layout as L
from easul.visual.element.container import CardContainer, HorizContainer, VerticalContainer
from easul.visual.element.markup import Message

#
# def test_creating_layout_with_horiz_container():
#     int_lo = create.layout_from_rows(rows=[
#         {"level":1,"type":"horiz_container","name":"hc"},
#          {"level":2, "type":"heading","title":"Factor bars"},
#          {"level":2,"type":"bullet_points","items":["My item 1","My item 2"]}], element_catalog = E.interpret_elements)
#     output = R.visual_to_html(int_lo)
#     assert isinstance(int_lo, L.InterpretLayout)
#     assert output.find("hcontainer")>-1
#     assert output.find("My item 1")>-1



def test_creating_layout_with_nested_container():
    int_vs = Visual(
        elements = [
            CardContainer(title="Individual", name="cc2", heading_level=5, elements = [
                HorizContainer(name="hc1", elements = [
                    Message(title="ROC curve"),
                    VerticalContainer(name="cn", elements = [
                        Message(title="Accurate"),
                        Message(title="Balanced")
                ])
            ])
        ])
    ])
    renderer = R.PlainRenderer()
    observed_html = renderer.create(int_vs).replace("\n", "").replace("\t", "").strip()

    expected_html = """
<div id="cc2" name="cc2" style="" class="card my-3"><div class="card-header"><h5 class="card-title">Individual</h5></div><div class="card-body"><div class="py-2"><div id="hc1" name="hc1" style="" class="row hcontainer "><div class="col-sm-auto px-3 pb-3"><div class=\'alert alert-success\'>ROC curve</div></div><div class="col-sm-auto px-3 pb-3"><div id="cn" name="cn" style="" class="vcontainer "><div class="py-2"><div class=\'alert alert-success\'>Accurate</div></div><div class="py-2"><div class=\'alert alert-success\'>Balanced</div></div></div></div></div></div></div></div>
""".strip()

    assert str(observed_html).find(expected_html) > -1