# -*- coding: utf-8 -*-
"""Qt wizard on linear thermic study case
"""

from PyQt4 import QtGui as qt
from PyQt4 import QtCore as qtc

import aster_s.salome_tree as ST
from aster_s.wizards import linear_thermic as LT

import aster_s_gui.wizards.common as WC
import aster_s.wizards.common as WCD
from aster_s.utils import log_gui


class SMeshExp(WC.CompoExp):
    """Linear thermic SMESH explorator
    """

    def __init__(self):
        WC.CompoExp.__init__(self)
        SMesh = ST.SMeshExplorator

        exp = SMesh()
        grp = exp.add_group(LT.GRP_NO)
        grp.register((2, 3), [SMesh.node])
        grp = exp.add_group(LT.GRP_MA)
        grp.register((2, 3), [SMesh.edge, SMesh.face])
        grp.register((3,), [SMesh.volume])
        self.register("imposed-temps", exp)

        exp = SMesh()
        grp = exp.add_group("stream")
        grp.register((2,), [SMesh.edge])
        grp.register((3,), [SMesh.face])
        self.register("stream", exp)

        exp = SMesh()
        grp = exp.add_group("source")
        grp.register((2,), [SMesh.face])
        grp.register((3,), [SMesh.volume])
        self.register("source", exp)

    def validate(self, mesh, mod):
        """Validate the mesh"""
        return WC.at_least_a_group(self.give("imposed-temps"), mesh, mod)


class GeomExp(WC.CompoExp):
    """Linear thermic GEOM explorator
    """

    def __init__(self):
        WC.CompoExp.__init__(self)
        Geom = ST.GeomExplorator

        exp = Geom()
        grp = exp.add_group(LT.GRP_NO)
        grp.register((2, 3), [Geom.vertex])
        grp = exp.add_group(LT.GRP_MA)
        grp.register((2, 3), [Geom.face, Geom.shell])
        grp.register((2,), [Geom.edge])
        grp.register((3,), [Geom.solid, Geom.compsolid])
        self.register("imposed-temps", exp)

        exp = Geom()
        grp = exp.add_group("stream")
        grp.register((2,), [Geom.edge])
        grp.register((3,), [Geom.face, Geom.shell])
        self.register("stream", exp)

        exp = Geom()
        grp = exp.add_group("source")
        grp.register((2,), [Geom.face, Geom.shell])
        grp.register((3,), [Geom.solid, Geom.compsolid])
        self.register("source", exp)

    def validate(self, mesh, mod):
        """Validate the mesh"""
        return WC.at_least_a_group(self.give("imposed-temps"), mesh, mod)


class ThermalConductance(WC.Param):
    """Thermal conductance coefficient
    """

    def __init__(self, dft="0.54"):
        self._dft = dft
        self.rangev = (0., 1e100)
        self.decs_nb = 10
        lamda_symb = u"\N{GREEK SMALL LETTER LAMDA}"
        self.title = u"Thermal conductivity (%s)" % lamda_symb
        self.suffix = u"(%s > 0)" % lamda_symb

    def add_to(self, page, grid, ridx):
        """Add to page and grid"""
        grid.addWidget(qt.QLabel(self.title), ridx, 0)
        minv, maxv = self.rangev
        entry = WC.create_entry(WC.Double(minv, maxv, self.decs_nb))
        #page.register_qt_field("th-conduct*", entry) modified by zxq at 2017/2/7
        entry.setText(self._dft)
        grid.addWidget(entry, ridx, 1)
        grid.addWidget(qt.QLabel(self.suffix), ridx, 2)


class TempPage(WC.WizardPage):
    """Page for defining imposed temperatures
    """

    def cleanupPage(self):
        """Clean page in case user navigates"""
        WC.WizardPage.cleanup(self)

    def initializePage(self):
        """Query the model on meshes"""
        WC.WizardPage.initialize(self)
        self.page.use(qt.QVBoxLayout())
        dims = [("T", 0.)]
        exp = self.give_field("exp-store").give_exp("imposed-temps")
        lst = exp.find_groups(self.give_field("mesh"))
        tit = u"Adding imposed temperatures on groups" 
        WC.add_condition_selector(self, lst, dims, "bound-temps*", tit)


def add_imposed_temps_page(wiz):
    """Add page on imposed temperatures"""
    page = wiz.add_page(u"Boundaries conditions", TempPage())
    page.register("bound-temps*", None)


class StreamPage(WC.WizardPage):
    """Page for defining streams normal to a face
    """

    def cleanupPage(self):
        """Clean page in case user navigates"""
        WC.WizardPage.cleanup(self)

    def initializePage(self):
        """Query the model on meshes"""
        WC.WizardPage.initialize(self)
        self.page.use(qt.QVBoxLayout())
        exp = self.give_field("exp-store").give_exp("stream")
        grps = exp.find_groups(self.give_field("mesh"))
        dims = [("Stream", 0.)]
        tit = u"Adding streams normal to a face (optional)"
        WC.add_condition_selector(self, grps, dims, "normal-streams", tit)


def add_normal_streams_page(wiz):
    """Add page on streams normal to a face"""
    page = wiz.add_page(u"Boundaries conditions", StreamPage())
    page.register("normal-streams", None)


class VolumicPage(WC.WizardPage):
    """Page for selecting volumic sources
    """

    def cleanupPage(self):
        """Clean page in case user navigates"""
        WC.WizardPage.cleanup(self)

    def initializePage(self):
        """Query the model on meshes"""
        WC.WizardPage.initialize(self)
        self.page.use(qt.QVBoxLayout())
        exp = self.give_field("exp-store").give_exp("source")
        grps = exp.find_groups(self.give_field("mesh"))
        dims = [("Source", 0.)]
        tit = u"Adding volumic sources (optional)"
        WC.add_condition_selector(self, grps, dims, "volumic-sources", tit)


def add_volumic_sources_page(wiz):
    """Add page on volumic sources"""
    page = wiz.add_page(u"Boundaries conditions", VolumicPage())
    page.register("volumic-sources", None)


class FinalPage(WC.FinalPage):
    """Build case
    """

    def validatePage(self):
        """Validate the wizard"""
        getf = self.give_field

        comm = LT.CommWriter()
        comm.use(LT.Modelisation(getf("model")))
        comm.use(LT.ThermalConductance(self.get_float("th-conduct")))
        th_consts = comm.use(LT.ThermalConstraints())

        temp_conds = th_consts.add(LT.TempConds())
        mesh = getf("mesh")
        exp = getf("exp-store").give_exp("imposed-temps")
        for gname, temp in getf("bound-temps"):
            gname = str(gname)
            grp_type = exp.give_group_key(mesh, gname)
            temp_conds.add(LT.TempImpo(grp_type, gname, temp))

        opt_fields = [
            ("normal-streams", LT.NormalStreams, LT.NormalStream),
            ("volumic-sources", LT.VolSources, LT.VolSource),
        ]
        for field_name, csts_cls, cst_cls in opt_fields:
            vals = getf(field_name)
            if not vals:
                continue
            csts = th_consts.add(csts_cls())
            for gname, val in vals:
                csts.add(cst_cls(gname, val))

        comm.write(self.get_str("command-file"))

        self.add_case("linear-thermic")
        return True


SIG = qtc.SIGNAL
connect = qtc.QObject.connect

class AstConditionsSelectorLT(WC.AstConditionsSelector):#added by zxq 温度条件
    def __init__(self, data, condition_type, parent):#condition_type 0 表示用于温度， 1 表示用于stream 2 用于volumic_sources  zxq 2017/2/9
        WC.AstConditionsSelector.__init__(self, data, condition_type, parent)
        
    def valid_by_group(self):
        if(self._data.grouptypesel != 0):
            cexp = self._data.exp_store
            if (self._condition_type == 0):
               exp = cexp.give_exp("imposed-temps")
               mesh = self._data.mesh
               grp_names = exp.find_groups(mesh)
               self._grp_names = grp_names
               dims = [("T", 0.)]
            elif (self._condition_type == 1):
               exp = cexp.give_exp("stream")
               mesh = self._data.mesh
               grp_names = exp.find_groups(mesh)
               self._grp_names = grp_names
               dims = [("Stream", 0.)]
            else:
               exp = cexp.give_exp("source")
               mesh = self._data.mesh
               grp_names = exp.find_groups(mesh)
               self._grp_names = grp_names
               dims = [("Source", 0.)]
               
            log_gui.debug("valid_by_group by group type %s, mesh %s", self._data.grouptypesel,mesh)
            if self._grp_names:
               head_names = [u"Group"] + [dim[0] for dim in dims]
               self._default_cond = [grp_names[0]] +  [dim[1] for dim in dims]
               self._tab.setItemDelegate(WC.ValueDelegate(self))
               #self._tab.setItemDelegateForColumn(0, WC.GroupDelegate(self, self._grp_names))
               
               model = WC.AstConditionsModel(self, head_names)
               self._tab.setModel(model)
               self._tab.setEnabled(True)
               self._tab.horizontalHeader().setClickable(True)
               if (dim[0] == "T"):
                  self.add_cond()
               icolumn = 0
               for iname in head_names:
                   width = 80
                   if icolumn > 0:
                      width = 60
                   self._tab.setColumnWidth(icolumn,width) 
                   icolumn += 1
               self.is_reseted = False          
            else:       
               self._build()     
        else:
            self._build()

class LTData():
    def __init__(self,mod):
        self.modellist = WCD.Model_Type_List(WCD.Analysis_Type.Linear_Thermic)
        self.itemindex = "defult"
        
        self.mesh = None
        self.mod = mod
        exp_store = WC.ExpStore()
        exp_store.register(WC.ExpStore.smesh, SMeshExp())
        exp_store.register(WC.ExpStore.geom, GeomExp())
        self.exp_store = exp_store
        self.grouptypesel = 0
        
    def get_dim(self):
        return self.get_sel_itm().dim
        
    def get_sel_itm(self):
        return (self.modellist.get_item(self.itemindex))
        
class Create_LTDock(qt.QDockWidget):
    def __init__(self, mod):
        desktop = mod.give_qtwid()
        qt.QDockWidget.__init__(self, desktop)
        self.data = LTData(mod)
        self.exp_store = self.data.exp_store
        
        self.setWindowTitle(u"Linear thmermic")
        centralWidget = qt.QWidget(self)
        vlayout = qt.QVBoxLayout()
        centralWidget.setLayout(vlayout)
        label_for_model = qt.QLabel(u"What kind of model do you want to work on?",self)
        vlayout.addWidget(label_for_model)
        
        model_sel = WC.AstModelSel(self.data,self)
        model_sel.place(vlayout)
       
        mesh_sel = WC.AstMeshSel(self.data,self)
        mesh_sel.place(vlayout)
        model_sel.add_related_component(mesh_sel)
        
        group_sel = WC.AstGroupTypeSel(self.data,self)
        connect(mesh_sel,SIG("mesh_valided"),group_sel.notify)
        model_sel.add_related_component(group_sel)

        group_sel.place(vlayout)
        
        vspacer = qt.QSpacerItem(20, 10, qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding)
        vlayout.addItem(vspacer)
       
        grid = qt.QGridLayout()
        tc = ThermalConductance()
        tc.add_to(qt.QWidget(), grid, 0)
        vlayout.addLayout(grid)
         
        vspacer = qt.QSpacerItem(20, 10, qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding)
        vlayout.addItem(vspacer)

        label_for_model = qt.QLabel(u"Adding imposed temperatures on groups",self)
        vlayout.addWidget(label_for_model)
        
        temps_sel = AstConditionsSelectorLT(self.data,0,self)
        connect(group_sel,SIG("group_valided"),temps_sel.valid_by_group)
        temps_sel.add_to(vlayout)
        
        vspacer = qt.QSpacerItem(20, 10, qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding)
        vlayout.addItem(vspacer)
        
        label_for_model = qt.QLabel(u"Adding streams normal to a face (optional)",self)
        vlayout.addWidget(label_for_model)
        
        stream_sel = AstConditionsSelectorLT(self.data,1,self)
        connect(group_sel,SIG("group_valided"),stream_sel.valid_by_group)
        stream_sel.add_to(vlayout)

        vspacer = qt.QSpacerItem(20, 10, qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding)
        vlayout.addItem(vspacer)
        
        label_for_model = qt.QLabel(u"Adding volumic sources (optional)",self)
        vlayout.addWidget(label_for_model)
        
        source_sel = AstConditionsSelectorLT(self.data,2,self)
        connect(group_sel,SIG("group_valided"),source_sel.valid_by_group)
        source_sel.add_to(vlayout)
        
        group_sel.add_related_component(temps_sel)
        group_sel.add_related_component(stream_sel)
        group_sel.add_related_component(source_sel)
        
        hlayout = qt.QHBoxLayout()
        hspacer = qt.QSpacerItem(27, 20, qt.QSizePolicy.Expanding, qt.QSizePolicy.Minimum)
        hlayout.addItem(hspacer)
        btnok = qt.QPushButton("OK",centralWidget)
        btncancel = qt.QPushButton("Cancel",centralWidget)
        hlayout.addWidget(btnok)
        hlayout.addWidget(btncancel)
        vlayout.addLayout(hlayout)
        self.setWidget(centralWidget)
        
def create_wizard(mod):
    """Create the linear thermic wizard"""
    wiz = WC.Wizard(u"Linear thermal analysis", mod)
    WC.add_model_page(wiz, [
        WC.Mode3D,
        WC.Plane,
        ])
    exp_store = WC.ExpStore()
    exp_store.register(WC.ExpStore.smesh, SMeshExp())
    exp_store.register(WC.ExpStore.geom, GeomExp())
    WC.add_mesh_page(wiz, mod, exp_store)
    title = u"Thermal conductivity definition"
    WC.add_material_page(wiz, title, [
        ThermalConductance(),
    ])
    add_imposed_temps_page(wiz)
    add_normal_streams_page(wiz)
    add_volumic_sources_page(wiz)
    WC.add_command_file_page(wiz, FinalPage(mod))
    return wiz


