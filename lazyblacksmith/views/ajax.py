from collections import OrderedDict
from flask import abort
from flask import Blueprint
from flask import json
from flask import jsonify
from flask import render_template
from flask import request
from sqlalchemy.orm import aliased
from sqlalchemy.orm.exc import NoResultFound

from lazyblacksmith.cache import cache
from lazyblacksmith.models import Item
from lazyblacksmith.models import Activity
from lazyblacksmith.models import ActivityProduct
from lazyblacksmith.models import ActivityMaterial
from lazyblacksmith.models import SolarSystem

ajax = Blueprint('ajax', __name__)

def is_not_ajax():
    """ 
    Return True if request is not ajax
    This function is used in @cache annotation to not cache direct call (http 403)
    """
    return not request.is_xhr


@ajax.route('/blueprint/search/<string:name>', methods=['GET'])
def blueprint_search(name):
    """
    Return JSON result for a specific search
    name is the request name.
    """
    if request.is_xhr:
        cache_key = 'blueprint:search:%s' % (name.lower().replace(" ", ""),)

        data = cache.get(cache_key)
        if data is None:
            blueprints = Item.query.filter(
                Item.name.ilike('%'+name.lower()+'%'),
                Item.max_production_limit.isnot(None)
            ).order_by(
                Item.name.asc()
            ).all()

            data = []
            for bp in blueprints: 
                invention = 0
                                      
                data.append([bp.id, bp.name, invention])
            
            # cache for 7 day as it does not change that often
            cache.set(cache_key, json.dumps(data), 24*3600*7)

        else:
            data = json.loads(data)

        return jsonify(result=data)
    else:
        return 'Cannot call this page directly', 403


@ajax.route('/blueprint/bom/<int:blueprint_id>', methods=['GET'])
@cache.memoize(timeout=3600*24*7, unless=is_not_ajax)
def blueprint_bom(blueprint_id):
    """
    Return JSON with the list of all bill of material for
    each material in the blueprint given in argument
    """
    if request.is_xhr:
        blueprints = ActivityMaterial.query.filter_by(
            item_id=blueprint_id, 
            activity=Activity.ACTIVITY_MANUFACTURING
        ).all()

        data = OrderedDict()
        for bp in blueprints:

            # As all item cannot be manufactured, catch the exception 
            try:
                bp_final = bp.material.product_for_activities
                bp_final = bp_final.filter_by(activity=Activity.ACTIVITY_MANUFACTURING).one()
                bp_final = bp_final.blueprint
            except NoResultFound:
                continue

            mats = bp_final.activity_materials.filter_by(activity=Activity.ACTIVITY_MANUFACTURING).all()

            if bp_final.id not in data:
                data[bp_final.id] = {
                    'id':bp.material.id,
                    'icon':bp_final.icon_32(),
                    'name':bp_final.name,
                    'materials':[],
                }

            for mat in mats:
                data[bp_final.id]['materials'].append({
                    'id':mat.material.id,
                    'name':mat.material.name,
                    'quantity':mat.quantity,
                    'icon':mat.material.icon_32(),
                })

        return jsonify(result=data)

    else:
        return 'Cannot call this page directly', 403


@ajax.route('/solarsystem/list', methods=['GET'])
@cache.cached(timeout=3600*24*7, unless=is_not_ajax)
def solarsystems():
    """
    Return JSON result with system list (ID,Name)
    """
    if request.is_xhr:
        systems = SolarSystem.query.all()
        data = []
        for system in systems:
            data.append(system.name)
        return jsonify(result=data)
    else:
        return 'Cannot call this page directly', 403
